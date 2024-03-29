#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Erik Anderson
# Email: erik.francis.anderson@gmail.com
# Date: 01/26/2021
"""Docstring for module __init__.py"""

# Imports - standard library
import os
from typing import Callable, List
import subprocess
from shutil import copy

# Imports - 3rd party packages
from toolbox.tool import Tool, ToolError
from toolbox.database import Database
from toolbox.logger import LogLevel
from toolbox.utils import *
from jinja2 import StrictUndefined, Environment, FileSystemLoader

# Imports - local source
from jinja_tool import JinjaTool
from toolbox_xilinx_tools.str_to_file import File, Section, SubSection


class XilinxImplementTool(JinjaTool):
    """Xilinx synthesis and implementation tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(XilinxImplementTool, self).__init__(db, log)
        self.bin = BinaryDriver("vivado")
        self.viv = self.get_db(self.get_namespace("XilinxImplementTool"))
        self.template_file = "templates/implement.tcl"
        self.render_file = os.path.join(self.get_db("internal.job_dir"),
                                        "implement.tcl")
        self.timing_xdc = File(
            os.path.join(self.get_db("internal.job_dir"), "timing.xdc"), "#")
        self.time_multiplier = {"us": 1e3, "ns": 1, "ps": 1e-3}
        self.open_tcl = os.path.join(self.get_db("internal.job_dir"), 'open.tcl')
        self.open_sh = os.path.join(self.get_db("internal.job_dir"), 'open.sh')

    def steps(self) -> List[Callable[[], None]]:
        """Returns a list of functions to run for each step"""
        return [self.render_tcl,
                self.render_timing_xdc,
                self.copy_includes,
                self.run_vivado]

    def copy_includes(self):
        """Copies all files from include directories to the build directory"""
        for d in self.viv["include_dirs"]:
            p = Path(d).glob('**/*')
            files = [x for x in p if x.is_file()]
            for f in files:
                copy(f, self.get_db("internal.job_dir"))
                self.log(f"Copied {f} to job dir")

    def render_tcl(self):
        """Renders tcl file that vivado will run in batch mode"""
        self.render_to_file(self.template_file, self.render_file, ts=self.ts)

    def add_primary_clock(self, fstr_obj, clk):
        """Primary clock dictionary. Adds lines to fstr_obj"""
        # Modify units
        if self.viv["units"]["time"] != "ns":
            clk["period"] = time_multiplier[self.viv["units"]
                                            ["time"]] * clk["period"]
            self.log(
                f'Clock "{clk["name"]}" period translated to Vivado time units: {clk["period"]} [ns]',
                LogLevel.WARNING)
            if "waveform" in clk:
                for j, edge in enumerate(clk["waveform"]):
                    edge = self.time_multiplier[self.viv["units"]
                                                ["time"]] * edge
                    self.log(
                        f'Clock "{clk["name"]}" edge {j} translated to Vivado time units: {edge} [ns]',
                        LogLevel.WARNING)
        # Add to section
        search_fun = "get_nets -hierarchical"
        if clk["type"] == "port":
            search_func = "get_ports"
        elif clk["type"] == "pin":
            search_func = "get_pins -hierarchical"
        if "waveform" in clk:
            clk["waveform"] = [str(edge) for edge in clk["waveform"]]
            fstr_obj.add_line(
                f"create_clock -name {clk['name']} -verbose -period {clk['period']} [{search_func} {clk['object']}] \\"
            )
            fstr_obj.add_line(f"\t-waveform {{{' '.join(clk['waveform'])}}}")
        else:
            fstr_obj.add_line(
                f"create_clock -name {clk['name']} -verbose -period {clk['period']} [{search_func} {clk['object']}]"
            )

    def add_generated_clock(self, fstr_obj, clk):
        """Generated clock dictionary. Adds lines to fstr_obj"""
        # Get search functions
        name_str = clk["object"]
        if clk["type"] == "port":
            name_str = f"[get_ports {clk['object']}]"
        elif clk["type"] == "pin":
            name_str = f"[get_pins -hierarchical {clk['object']}]"
        elif clk["type"] == "net":
            name_str = f"[get_nets -hierarchical {clk['object']}]"
        source_str = clk["source"]
        if clk["source_type"] == "port":
            source_str = f"[get_ports {clk['source']}]"
        elif clk["source_type"] == "pin":
            source_str = f"[get_pins -hierarchical {clk['source']}]"
        elif clk["source_type"] == "net":
            source_str = f"[get_nets -hierarchical {clk['source']}]"
        # Common lines
        fstr_obj.add_line(
            f"create_generated_clock -verbose -name {clk['name']} \\")
        fstr_obj.add_line(f"\t-source {source_str} \\")
        # Determine how clock is being defined
        if "edges" in clk and "edge_shift" in clk:
            for j, edge in enumerate(clk["edges"]):
                clk["edges"][j] = str(edge)
                clk["edge_shift"][j] = str(
                    self.time_multiplier[self.viv["units"]["time"]] *
                    clk["edge_shift"][j])
                if self.viv["units"]["time"] != "ns":
                    self.log(
                        f'Clock "{clk["name"]}" edge shift {j} translated to Vivado time units: {clk["edge_shift"][j]} [ns]',
                        LogLevel.WARNING)
            fstr_obj.add_line(f"\t-edges {{{' '.join(clk['edges'])}}} \\")
            fstr_obj.add_line(
                f"\t-edge_shift {{{' '.join(clk['edge_shift'])}}} \\")
        elif "multiplier" in clk:
            fstr_obj.add_line(f"\t-multiply_by {clk['multiplier']} \\")
        elif "divisor" in clk:
            fstr_obj.add_line(f"\t-divide_by {clk['divisor']} \\")
        else:
            self.log(
                f'Generated clock "{clk["name"]}" does not specify period and duty cycle',
                LogLevel.WARNING)
        fstr_obj.add_line(f"\t{name_str}")

    def io_delay_section(self):
        """Generates section with set_input_delay and set_output_delay constraints"""
        section = Section("Input/output delay constraints", "#")
        if self.viv["input_delay_constraints"]:
            section.add_line("# Input delays")
            for con in self.viv["input_delay_constraints"]:
                min_bin = BinaryDriver("set_input_delay")
                max_bin = BinaryDriver("set_input_delay")
                min_delay = con["min_delay"] * self.time_multiplier[
                    self.viv["units"]["time"]]
                max_delay = con["max_delay"] * self.time_multiplier[
                    self.viv["units"]["time"]]
                if self.viv["units"]["time"] != "ns":
                    self.log(
                        "Input delay translated from {con['min_delay']} {self.viv['units']['time']} to {min_delay} ns"
                    )
                    self.log(
                        "Input delay translated from {con['max_delay']} {self.viv['units']['time']} to {max_delay} ns"
                    )
                if con["clock_edge"] == "fall":
                    min_bin.add_option("-clock_fall")
                    max_bin.add_option("-clock_fall")
                min_bin.add_option("-verbose")
                max_bin.add_option("-verbose")
                min_bin.add_option("-clock", f"[get_clocks {con['clock']}]")
                max_bin.add_option("-clock", f"[get_clocks {con['clock']}]")
                min_bin.add_option("-min", f"{min_delay}")
                max_bin.add_option("-max", f"{max_delay}")
                min_bin.add_option(f"[get_ports {con['port']}]")
                max_bin.add_option(f"[get_ports {con['port']}]")
                section.add_line(min_bin.get_execute_string())
                section.add_line(max_bin.get_execute_string())
        if self.viv["output_delay_constraints"]:
            section.add_line("# Output delays")
            for con in self.viv["output_delay_constraints"]:
                min_bin = BinaryDriver("set_output_delay")
                max_bin = BinaryDriver("set_output_delay")
                min_delay = con["min_delay"] * self.time_multiplier[
                    self.viv["units"]["time"]]
                max_delay = con["max_delay"] * self.time_multiplier[
                    self.viv["units"]["time"]]
                if self.viv["units"]["time"] != "ns":
                    self.log(
                        "Output delay translated from {con['delay']} {self.viv['units']['time']} to {delay} ns"
                    )
                if con["clock_edge"] == "fall":
                    min_bin.add_option("-clock_fall")
                    max_bin.add_option("-clock_fall")
                min_bin.add_option("-verbose")
                max_bin.add_option("-verbose")
                min_bin.add_option("-clock", f"[get_clocks {con['clock']}]")
                max_bin.add_option("-clock", f"[get_clocks {con['clock']}]")
                min_bin.add_option("-min", f"{min_delay}")
                max_bin.add_option("-max", f"{max_delay}")
                min_bin.add_option(f"[get_ports {con['port']}]")
                max_bin.add_option(f"[get_ports {con['port']}]")
                section.add_line(min_bin.get_execute_string())
                section.add_line(max_bin.get_execute_string())
        return section

    def clock_groups(self):
        """Generates clock groups"""
        section = Section("Clock groups", "#")
        for cg in self.viv["clock_groups"]:
            section.add_line(f"set_clock_groups -name {cg['name']} -{cg['type']} \\")
            for i, group in enumerate(cg["groups"]):
                if i == len(cg["groups"]) - 1:
                    section.add_line(f'-group [get_clocks -include_generated_clocks "{" ".join(group)}"]')
                else:
                    section.add_line(f'-group [get_clocks -include_generated_clocks "{" ".join(group)}"] \\')
        return section

    def false_paths(self):
        """Generates clock groups"""
        section = Section("False Paths", "#")
        for path in self.viv["false_paths"]:
            if path["from"]['type'] == "clock":
                from_search = "get_clocks"
            if path["to"]['type'] == "port":
                to_search = "get_ports"
            elif path["to"]['type'] == "pin":
                to_search = "get_pins -hierarchical"
            section.add_line(f"set_false_path -verbose \\")
            section.add_line(f"\t-from [{from_search} {path['from']['name']}] \\")
            section.add_line(f"\t-to [{to_search} {path['to']['name']}]")
        return section

    def render_timing_xdc(self):
        """Renders timing xdc file for constraining timing pre-synthesis"""
        # TODO create similar methods for all xdc types: timing, io, misc, waver, and physical
        # TODO delete me! Or put in different section? This causes a warning
        ## Units section
        #units_sec = Section(
        #    "Set Units (redefine units in every XDC because paranoia)", "#")
        #units_sec.add_line(f"set_units -verbose \\")
        #units_sec.add_line(f"\t-current {self.viv['units']['current']} \\")
        #units_sec.add_line(f"\t-voltage {self.viv['units']['voltage']} \\")
        #units_sec.add_line(f"\t-power {self.viv['units']['power']} \\")
        #units_sec.add_line(
        #    f"\t-resistance {self.viv['units']['resistance']} \\")
        #units_sec.add_line(f"\t-altitude {self.viv['units']['altitude']}")
        #self.timing_xdc.add(units_sec)
        # Primary Clocks section
        clocks_sec = Section("Clock definitions", "#")
        self.timing_xdc.add(clocks_sec)
        if self.viv["primary_clocks"]:
            clocks_sec.add_line("# Primary clocks")
            for clk in self.viv["primary_clocks"]:
                self.add_primary_clock(clocks_sec, clk)
        if self.viv["generated_clocks"]:
            clocks_sec.add_line("# Generated clocks")
            for clk in self.viv["generated_clocks"]:
                self.add_generated_clock(clocks_sec, clk)
        # Input/output delay
        self.timing_xdc.add(self.io_delay_section())
        # Clock groups
        self.timing_xdc.add(self.clock_groups())
        self.timing_xdc.add(self.false_paths())
        # Generate file
        if self.timing_xdc.generate():
            self.log(f"Timing XDC generated: {self.timing_xdc.fpath.relative_to(self.get_db('internal.work_dir'))}")
        else:
            self.log(f"Timing XDC not generated",
                     LogLevel.WARNING)

    def run_vivado(self):
        """Actually runs the vivado command"""
        if self.viv["execute"]:
            self.log('Assumes "vivado" binary added to path')
            # Add options
            render_file_local = Path(self.render_file).relative_to(
                self.get_db('internal.job_dir'))
            self.bin.add_option("-mode", self.viv['mode'])
            self.bin.add_option("-source", render_file_local)
            # Execute binary
            self.log(self.bin.get_execute_string())
            self.bin.execute(directory=self.get_db('internal.job_dir'))
            self.log(
                f"Final implementation in => {Path(self.get_db('internal.job_dir')).relative_to(self.get_db('internal.work_dir'))}"
            )
            # Open design script
            with open(self.open_sh, 'w') as fp:
                fp.write('#!/usr/bin/env bash\n')
                fp.write(f'vivado -mode tcl -source {self.open_tcl}')
            os.chmod(self.open_sh, 0o755)
            checkp = os.path.join(self.get_db('internal.job_dir'), 'checkpoints/post_route.dcp')
            with open(self.open_tcl, 'w') as fp:
                fp.write(f'open_checkpoint {checkp}\n')
                fp.write('start_gui')
            self.log("Open design with script: build/implement/current/open.sh")
        else:
            self.log(
                "Xilinx implement execute flag set to false. Design not implemented."
            )
