#!/usr/bin/env bash

# Set PYTHONPATH accordingly
if [ -z "$PYTHONPATH" ]
then
    export PYTHONPATH=$PWD
else
    export PYTHONPATH=$PWD:$PYTHONPATH
fi

# Set MYPYPATH accordingly
if [ -z "$MYPYPATH" ]
then
    export MYPYPATH=$PWD/toolbox_xilinx_tools
else
    export MYPYPATH=$PWD/toolbox_xilinx_tools:$MYPYPATH
fi

# Set TOOLBOX-XILINX-TOOLS_HOME variable
export TOOLBOX_XILINX_TOOLS_HOME=$PWD
