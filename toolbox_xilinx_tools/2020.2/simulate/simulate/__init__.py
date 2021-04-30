#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Erik Anderson
# Email: erik.francis.anderson@gmail.com
# Date: 03/03/2020
"""Docstring for module __init__.py"""

# Imports - standard library
import os
from typing import Callable, List
from jinja2 import StrictUndefined, Environment, FileSystemLoader

# Imports - 3rd party packages
from toolbox.tool import Tool, ToolError
from toolbox.database import Database
from toolbox.logger import LogLevel
from toolbox.utils import *

# Imports - local source
from jinja_tool import JinjaTool


class XsimTool(Tool):
    """Xcelium toolbox tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(XsimTool, self).__init__(db, log)
        # Create binary driver
        self.sim = self.get_db(self.get_namespace("XsimTool"))

    def steps(self) -> List[Callable[[], None]]:
        return [self.parse_files, self.elaborate_design, self.simulate_design]

    def parse_files(self):
        """Parsing design files with xvhdl and xvlog"""
        vlog_bin = BinaryDriver("xvlog")
        #vlog_bin.add_option("-verbose", 2)
        #if self.sim["include_uvm"]:
        #    vlog_bin.add_option("-lib UVM")
        if self.sim["verilog_version"] == "sv":
            vlog_bin.add_option("-sv")
        for f in self.sim["defines"]:
            vlog_bin.add_option(f"{Path(f).resolve()}")
        for f in self.sim["packages"]:
            vlog_bin.add_option(f"{Path(f).resolve()}")
        for f in self.sim["test"]:
            vlog_bin.add_option(f"{Path(f).resolve()}")
        for f in self.sim["rtl"]:
            vlog_bin.add_option(f"{Path(f).resolve()}")
        for d in self.sim["include_dirs"]:
            vlog_bin.add_option("-include", f"{Path(d).resolve()}")
        # Execute
        self.log(vlog_bin.get_execute_string())
        exec_dir = self.get_db('internal.job_dir')
        vlog_bin.execute(directory=exec_dir)

    def elaborate_design(self):
        """Elaborate design with xelab"""
        elab_bin = BinaryDriver("xelab")
        elab_bin.add_option(f"work.{self.sim['testbench']}")
        elab_bin.add_option("-snapshot", self.sim['testbench'])
        elab_bin.add_option("-debug", "all")
        #if self.sim["include_uvm"]:
        #    elab_bin.add_option("-lib UVM")
        # Execute
        self.log(elab_bin.get_execute_string())
        exec_dir = self.get_db('internal.job_dir')
        elab_bin.execute(directory=exec_dir)

    def simulate_design(self):
        """Simulate design with xsim"""
        sim_bin = BinaryDriver("xsim")
        #if self.sim["include_uvm"]:
        #    sim_bin.add_option("-lib UVM")
        # Append options raw
        for o in self.sim["options"]:
            sim_bin.add_option(value=o)
        sim_bin.add_option(self.sim["testbench"])
        #sim_bin.add_option("-runall")
        sim_bin.add_option("-wdb", "waves")
        sim_bin.add_option("-gui")
        # Execute
        self.log(sim_bin.get_execute_string())
        exec_dir = self.get_db('internal.job_dir')
        sim_bin.execute(directory=exec_dir)
