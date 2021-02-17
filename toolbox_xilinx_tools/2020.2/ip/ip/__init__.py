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
from toolbox_xilinx_tools.str_to_file import File, Section


class IPTool(Tool):
    """IP generator toolbox tool"""
    def __init__(self, db: Database, log: Callable[[str, LogLevel], None]):
        super(IPTool, self).__init__(db, log)
        # Create binary driver
        self.ip = self.get_db(self.get_namespace("IPTool"))
        self.bin = BinaryDriver(self.ip["bin"])
        self.ip_file = File(
            os.path.join(self.get_db("internal.job_dir"), "ip.tcl"), "#")

    def steps(self) -> List[Callable[[], None]]:
        return [self.render_ip_tcl, self.run_vivado]

    def render_ip_tcl(self):
        """Generates tcl that will be passed to vivado"""
        self.ip_file.add_line(f"set_part {self.ip['part']}")
        for name, block in self.ip["blocks"].items():
            sec = Section(f"{name}: {block['vlnv']}", "#")
            self.ip_file.add(sec)
            sec.add_line(
                f"create_ip -vlnv {block['vlnv']} -module_name {name}")
            for prop in block["properties"]:
                sec.add_line(
                    f"set_property CONFIG.{prop['name']} {prop['value']}")
            sec.add_line(f"generate_target all [get_ips {name}]")
            sec.add_line(f"synth_ip [get_ips {name}]")
            #sec.add_line(f"lsearch -all -inline [list_property [get_ips {name}]] CONFIG.*")
            sec.add_line(f"report_property [get_ips {name}]")
        if self.ip_file.generate():
            self.log(f"File generated: {self.ip_file.fpath}")
        else:
            self.log(f"File not generated: {self.ip_file.fpath}",
                     LogLevel.WARNING)

    def run_vivado(self):
        """Actually runs the vivado command"""
        if self.ip["execute"]:
            # Add options
            self.bin.add_option("-mode", "batch")
            self.bin.add_option("-source", self.ip_file.fpath)
            # Execute binary
            self.log(self.bin.get_execute_string())
            self.bin.execute(directory=self.get_db('internal.job_dir'))
            self.log(
                f"Final implementation in => {Path(self.get_db('internal.job_dir')).relative_to(self.get_db('internal.work_dir'))}"
            )
        else:
            self.log(
                "IP generation execute flag set to false. IP not generated.")
