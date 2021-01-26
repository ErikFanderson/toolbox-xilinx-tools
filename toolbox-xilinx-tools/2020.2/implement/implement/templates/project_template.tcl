create_project wave_gen <dir> <something> <something> <something>

set_property board_part xilinx.com:... [current_project]

add_files <verilog files>

get_filesets

# Import IP
import_ip <ip .sci file>
import_ip <ip .sci file>

# Add constraints and testbench files?
add_files -fileset constrs_1 <constraints_file>
add_files -fileset sim_1 <testbench_file>

# Not sure what this does
update_compile_order -fileset sim_1
update_compile_order -fileset sources_1

# Run synthesis
launch_runs synth_1
wait_on_run synth_1

# Open and report synthesis run
open_run synth_1 netlist_1
report_timing_summary -file <dest_file>

# Run implementation
launch_runs impl_1
wait_on_run impl_1

# Generate bitstream
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

# Open and report implementation
open_run impl_1
report_utilization -file <dest_file>
