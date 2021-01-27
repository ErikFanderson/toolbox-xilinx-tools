# Read source files and constraints 
{% for f in ts.vivado.verilog %}
read_verilog {{f|realpath}}
{% endfor %}
{% for f in ts.vivado.vhdl %}
read_vhdl {{f|realpath}}
{% endfor %}
{% for f in ts.vivado.xdc %}
read_xdc {{f|realpath}}
{% endfor %}

# Pin Planning (TODO should this be in an xdc file?? These commands are in tcl reference though)
#create_interface
#make_diff_pair_ports
#resize_port_bus
#create_port
#place_ports
#set_package_pin_val
#delete_interface
#remove_port
#split_diff_pair_ports

# Synthesis
synth_design -top {{ts.vivado.top}} -part {{ts.vivado.part}}
file mkdir checkpoints
write_checkpoint -verbose checkpoints/post_synth.dcp  
report_timing_summary -file reports/post_synth_timing.rpt
report_utilization -file reports/post_synth_util.rpt
# TODO add more reports? They show example of custom script to report critical paths

# Post-Synth Optimization 
opt_design
report_timing_summary -file reports/post_opt_timing.rpt
report_utilization -file reports/post_opt_util.rpt
# TODO add more reports? They show example of custom script to report critical paths

# Placement (TODO why is report_clock_utilization done before phys_opt_design?)
place_design
report_clock_utilization -file reports/post_place_clock_util.rpt
# TODO optionally run optimization if there are timing violations after placement
if {[get_property SLACK [get_timing_paths -max_paths 1 -nworst -setup]] < 0} {
    puts "Found setup timing violations => running physical optimization"
    phys_opt_design
}
write_checkpoint -verbose checkpoints/post_place.dcp
report_timing_summary -file reports/post_place_timing.rpt
report_utilization -file reports/post_place_util.rpt

# Route
route_design
write_checkpoint checkpoints/post_route.dcp
report_route_status -file reports/post_route_status.rpt
report_timing_summary -file reports/post_route_timing.rpt
report_power -file reports/post_route_power.rpt
report_drc -file reports/post_route_drc.rpt
write_verilog -mode timesim -sdf_anno true {{ts.vivado.top}}_post_impl.v
