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

# Imports - 3rd party packages
from toolbox.tool import Tool, ToolError
from toolbox.database import Database
from toolbox.logger import LogLevel
from toolbox.utils import *
from jinja2 import StrictUndefined, Environment, FileSystemLoader

# Imports - local source
from jinja_tool import JinjaTool


class XilinxImplementTool(JinjaTool):
    """Xilinx synthesis and implementation tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(XilinxImplementTool, self).__init__(db, log)
        self.bin = BinaryDriver("vivado")
        self.viv = self.get_db(self.get_namespace("XilinxImplementTool"))
        self.template_file = "templates/implement.tcl"
        self.render_file = os.path.join(self.get_db("internal.job_dir"),
                                        "implement.tcl")

    def steps(self) -> List[Callable[[], None]]:
        """Returns a list of functions to run for each step"""
        return [self.render_tcl, self.render_timing_xdc, self.run_vivado]

    def render_tcl(self):
        """Renders tcl file that vivado will run in batch mode"""
        self.render_to_file(self.template_file,
                            self.render_file,
                            ts=self.ts)
    
    def render_timing_xdc(self):
        """Renders timing xdc file for constraining timing pre-synthesis"""
        # TODO create similar methods for all xdc types: timing, io, misc, waver, and physical
        # Path setup
        template_file = "timing.xdc" 
        render_file = os.path.join(self.get_db("internal.job_dir"), "timing.xdc")
        # Adjust clock units
        time_multiplier = {"us": 1e3, "ns": 1, "ps": 1e-3}
        for i, clk in enumerate(self.viv["clocks"]):
            clk["period"] = time_multiplier[self.viv["units"]["time"]]*clk["period"] 
            if self.viv["units"]["time"] != "ns":
                self.log(f'Clock "{clk["name"]}" period translated to Vivado time units: {clk["period"]} [ns]', LogLevel.WARNING)
        # Render file
        self.render_to_file(template_file,
                            render_file,
                            clocks=self.viv["clocks"],
                            ts=self.ts)

    def run_vivado(self):
        """Actually runs the vivado command"""
        if self.viv["execute"]:
            self.log('Assumes "vivado" binary added to path')
            # Add options
            render_file_local = Path(self.render_file).relative_to(
                self.get_db('internal.job_dir'))
            self.bin.add_option("-mode", "batch")
            self.bin.add_option("-source", render_file_local)
            # Execute binary
            self.log(self.bin.get_execute_string())
            self.bin.execute(directory=self.get_db('internal.job_dir'))
            self.log(
                f"Final implementation in => {Path(self.get_db('internal.job_dir')).relative_to(self.get_db('internal.work_dir'))}"
            )
        else:
            self.log(
                "Xilinx implement execute flag set to false. Design not implemented."
            )
