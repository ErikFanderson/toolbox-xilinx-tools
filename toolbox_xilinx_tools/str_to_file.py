#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Erik Anderson
# Email: erik.francis.anderson@gmail.com
# Date: 02/04/2021
"""Docstring for module str_to_file"""

# Imports - standard library
from pathlib import Path
from abc import ABC, abstractmethod
import getpass
from datetime import date

# Imports - 3rd party packages

# Imports - local source


class FileStr(ABC):

    def __init__(self, comment_char = "//"):
        self._fstrings = []
        self._comment_char = comment_char

    def add(self, something):
        self._fstrings.append(something)
    
    def pre_to_str(self):
        return "" 
    
    def post_to_str(self):
        return "" 

    def add_line(self, line, comment=None):
        """Convenience method for line"""
        line = Line(line, comment, self._comment_char)
        self.add(line)
    
    def to_str(self):
        """Stringify me!"""
        rstr = self.pre_to_str() 
        for obj in self._fstrings:
            rstr += obj.to_str()
        rstr += self.post_to_str() 
        return rstr


class File(FileStr):
    """Top level file str"""
    
    def __init__(self, fpath, comment_char = "//"):
        """Creates file object that can be output to file
        name is a str that the file should be output to
        """
        super(File, self).__init__(comment_char)
        self._fpath = Path(fpath).resolve()

    @property
    def fpath(self):
        return self._fpath

    def pre_to_str(self):
        today = date.today()
        rstr = f"{self._comment_char}{'='*(80-len(self._comment_char))}\n"
        rstr += f"{self._comment_char} User: {getpass.getuser()}\n"
        rstr += f"{self._comment_char} Date: {today.strftime('%m/%d/%y')}\n"
        rstr += f"{self._comment_char} Path: {self._fpath}\n"
        rstr += f"{self._comment_char}{'='*(80-len(self._comment_char))}\n"
        return rstr
    
    def generate(self, overwrite = False):
        """Creates a file at fpath with all sections, subsections, and headers"""
        if self._fpath.exists() and not overwrite:
            return False
        else:
            with open(self._fpath, "w")as fp:
                fp.write(self.to_str())
            return True

class Section(FileStr):
    """A portion of a file"""
    def __init__(self, comment, comment_char = "//"):
        """Creates a section with a comment"""
        super(Section, self).__init__(comment_char)
        self._comment = comment 
    
    def pre_to_str(self):
        today = date.today()
        rstr = f"{self._comment_char}{'-'*(80-len(self._comment_char))}\n"
        rstr += f"{self._comment_char} {self._comment}\n"
        rstr += f"{self._comment_char}{'-'*(80-len(self._comment_char))}\n"
        return rstr
    
    def post_to_str(self):
        rstr = f"{self._comment_char}{'-'*(80-len(self._comment_char))}\n"
        return rstr
    
class SubSection(FileStr):
    """A portion of a file"""
    def __init__(self, comment, comment_char = "//"):
        """Creates a section with a comment"""
        super(SubSection, self).__init__(comment_char)
        self._comment = comment 
    
    def pre_to_str(self):
        today = date.today()
        rstr = f"{self._comment_char} {self._comment}\n"
        return rstr
    
class Line(FileStr):
    """Single line. Smallest file string unit"""
    def __init__(self, line, comment = None, comment_char = "//"):
        super(Line, self).__init__(comment_char)
        self._comment = comment
        if self._comment:
            self._line = f"{line} {comment_char} {comment}\n"
        else:
            self._line = line + "\n"

    def to_str(self):
        return self._line

if __name__ == '__main__':
    f = File("test.tcl")
    section = Section("Test Section")
    subsection = SubSection("Test SubSection")
    section.add(subsection) 
    f.add_line("0", "test comment")
    f.add(section)
    subsection.add_line("test line 0")
    subsection.add_line("test line 1")
    section.add_line("test line 1")
    print(f.to_str())
