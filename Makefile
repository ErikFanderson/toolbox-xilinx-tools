# Author: Erik Anderson 
# Date Created: 01/22/2021

default: test

# Lints toolbox_xilinx_tools directory recursively
lint:
	pylint toolbox_xilinx_tools tests

# Formats toolbox_xilinx_tools directory recursively
format:
	yapf -i -r toolbox_xilinx_tools tests

# Type checks toolbox_xilinx_tools directory recursively
type:
	mypy toolbox_xilinx_tools tests

# Runs all tests in tests directory 
test:
	pytest -v tests

# Export anaconda environment
export:
	conda env export --from-history | grep -v "prefix" > environment.yml
