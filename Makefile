# Author: Erik Anderson 
# Date Created: 01/22/2021

default: test

# Lints toolbox-xilinx-tools directory recursively
lint:
	pylint toolbox-xilinx-tools tests

# Formats toolbox-xilinx-tools directory recursively
format:
	yapf -i -r toolbox-xilinx-tools tests

# Type checks toolbox-xilinx-tools directory recursively
type:
	mypy toolbox-xilinx-tools tests

# Runs all tests in tests directory 
test:
	pytest -v tests

# Export anaconda environment
export:
	conda env export --from-history | grep -v "prefix" > environment.yml
