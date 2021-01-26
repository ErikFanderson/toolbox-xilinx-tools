#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Erik Anderson
# Email: erik.francis.anderson@gmail.com
# Date: 03/03/2020
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
from cadence_tool import CadenceTool
from jinja_tool import JinjaTool


class LiberateTool(CadenceTool, JinjaTool):
    """Genus toolbox tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(LiberateTool, self).__init__(db, log)
        self.bin = BinaryDriver(
            self.get_db(self.get_namespace("LiberateTool") + ".bin"))
        self.lib = self.get_db(self.get_namespace("LiberateTool"))

    def steps(self) -> List[Callable[[], None]]:
        """Returns a list of functions to run for each step"""
        return [self.render_libgen, self.run_liberate]

    @property
    def libgen_template(self):
        return self.get_db(
            self.get_namespace("LiberateTool") + ".libgen_template")

    @property
    def libgen(self):
        return os.path.join(self.get_db("internal.job_dir"), "libgen.tcl")

    def get_input_slew(self):
        """Translates units into the liberate default 1ns"""
        base_unit = 1e-9
        units = {"1ns": 1e-9, "100ps": 1e-10, "10ps": 1e-11, "1ps": 1e-12}
        pre_scaler = units[self.lib["time_unit"]]
        input_slew = self.lib["input_slew"]
        return [round(s * pre_scaler / base_unit, 10) for s in input_slew]

    def get_output_load(self):
        """Translates units into the liberate default 1pF"""
        base_unit = 1e-12
        units = {"1pf": 1e-12, "100ff": 1e-13, "10ff": 1e-14, "1ff": 1e-15}
        pre_scaler = units[self.lib["cap_unit"]]
        output_load = self.lib["output_load"]
        return [round(o * pre_scaler / base_unit, 10) for o in output_load]

    def render_libgen(self):
        """Renders abstract replay and option files"""
        # Unit translation
        input_slew = self.get_input_slew()
        output_load = self.get_output_load()
        # Lib name
        cell = self.lib["cell"]
        volt = self.lib["voltage"]
        temp = self.lib["temperature"]
        lib_name = f"{cell}_v{volt}_t{temp}"
        if self.lib["lib_name"]:
            lib_name = self.lib["lib_name"]
        # Get pinlist
        pin_list = []
        for k, v in self.lib["cell_pins"].items():
            pin_list += v
        self.render_to_file(self.libgen_template,
                            self.libgen,
                            lib_name=lib_name,
                            input_slew=input_slew,
                            pin_list=pin_list,
                            output_load=output_load,
                            ts=self.ts)

    def run_liberate(self):
        if self.get_db(self.get_namespace("LiberateTool") + ".execute"):
            # Add options
            self.bin.add_option(self.libgen)
            # Execute binary
            self.log(self.bin.get_execute_string())
            self.bin.execute(directory=self.get_db('internal.job_dir'))
            self.log(
                f"Final liberate results in => {Path(self.get_db('internal.job_dir')).relative_to(self.get_db('internal.work_dir'))}"
            )
        else:
            self.log(
                "Liberate execute flag set to false. Lib generation not performed."
            )
