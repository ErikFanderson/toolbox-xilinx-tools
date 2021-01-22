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
    export MYPYPATH=$PWD/toolbox-xilinx-tools
else
    export MYPYPATH=$PWD/toolbox-xilinx-tools:$MYPYPATH
fi

# Set TOOLBOX-XILINX-TOOLS_HOME variable
export TOOLBOX-XILINX-TOOLS_HOME=$PWD
