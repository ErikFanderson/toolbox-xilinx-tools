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


class XsimTool(JinjaTool):
    """Xcelium toolbox tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(XsimTool, self).__init__(db, log)
        # Create binary driver
        self.xsim = self.get_db(self.get_namespace("simulate"))
        self.bin = BinaryDriver(self.xsim["bin"])

    def steps(self) -> List[Callable[[], None]]:
        return [self.render_sim_tcl, self.run_xrun]

    def render_sim_tcl(self):
        """Generates tcl that will be passed to xrun"""
        if self.xcelium["top_tcl_template"]:
            self.add_jinja_templates([self.xcelium["top_tcl_template"]])
            template = self.xcelium["top_tcl_template"]
            output = os.path.join(self.get_db('internal.job_dir'),
                                  Path(template).name)
            self.render_to_file(template,
                                output,
                                xcelium=self.xcelium,
                                user=self.get_db("user"))

    def append_files(self, fnames: List[str]):
        """Iterates through file and appends valid ones to exec call"""
        for f in fnames:
            self.bin.add_option(value=str(Path(f).resolve()))

    def run_xrun(self):
        """Calls xrun"""
        # Append files
        self.append_files(self.xcelium["defines"])
        self.append_files(self.xcelium["packages"])
        self.append_files(self.xcelium["rtl"])
        self.append_files(self.xcelium["test"])
        # include dirs
        if self.xcelium["include_dirs"]:
            incdirs = [
                str(Path(d).resolve()) for d in self.xcelium["include_dirs"]
            ]
            self.bin.add_option(flag="-incdir", value=" ".join(incdirs))
        # Append options raw
        for o in self.xcelium["options"]:
            self.bin.add_option(value=o)
        self.bin.add_option(flag='-top', value=self.xcelium["testbench"])
        # Append TCL if it exists
        if self.xcelium["top_tcl_template"]:
            template = self.xcelium["top_tcl_template"]
            sim_tcl = os.path.join(self.get_db('internal.job_dir'),
                                   Path(template).name)
            self.bin.add_option(flag='-input', value=sim_tcl)
        # Execute binary
        self.log(self.bin.get_execute_string())
        self.bin.execute(directory=self.get_db('internal.job_dir'))
