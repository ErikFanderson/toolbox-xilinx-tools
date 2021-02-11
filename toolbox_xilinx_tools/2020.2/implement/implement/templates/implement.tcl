#------------------------------------------------------------------------------
# Read source files and constraints 
#------------------------------------------------------------------------------
# Source files and any extra xdc files
{% for f in ts.vivado.verilog %}
read_verilog -verbose {{f|realpath}}
{% endfor %}
{% for f in ts.vivado.vhdl %}
read_vhdl -verbose {{f|realpath}}
{% endfor %}
{% for f in ts.vivado.xdc %}
read_xdc -verbose {{f|realpath}}
{% endfor %}

# Timing constraints
read_xdc -verbose timing.xdc

# Create directories 
file mkdir checkpoints
file mkdir reports
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Synthesis (sets top and opens design)
#------------------------------------------------------------------------------
synth_design -top {{ts.vivado.top}} -part {{ts.vivado.part}}
write_checkpoint -force -verbose checkpoints/post_synth.dcp  
report_timing_summary -file reports/post_synth_timing.rpt
report_utilization -file reports/post_synth_util.rpt
# TODO add more reports? They show example of custom script to report critical paths
write_verilog -force {{ts.vivado.top}}_post_synth.v
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Set Units (set once after synthesis - requires open design)
#------------------------------------------------------------------------------
set_units -verbose \
    -capacitance {{ts.vivado.units.capacitance}} \
    -current {{ts.vivado.units.current}} \
    -voltage {{ts.vivado.units.voltage}} \
    -power {{ts.vivado.units.power}} \
    -resistance {{ts.vivado.units.resistance}} \
    -altitude {{ts.vivado.units.altitude}}
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# TODO Device configuration setup (specifies how device configuration is stored and loaded)
# TODO place this in xdc file? physical.xdc
#------------------------------------------------------------------------------
# Configuration bank voltage select (CFGBVS) 
# CFGBVS => VCCO when CONFIG_VOLTAGE = 3.3V/2.5V
# CFGBVS => GND when CONFIG_VOLTAGE = 1.8V/1.5V
set_property CFGBVS {{ts.vivado.config.bank_voltage_select}} [current_design]
set_property CONFIG_VOLTAGE {{ts.vivado.config.voltage}} [current_design]

# From UG899
# Use below commands to initially set the configuration mode
set_property BITSTREAM.CONFIG.PERSIST NO [current_design]
set_property CONFIG_MODE {{ts.vivado.config.mode}} [current_design]

## TODO if you want config to persist then add below line after above commands
#set_property BITSTREAM.CONFIG.PERSIST YES [current_design]
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# IO/Pin Planning 
#------------------------------------------------------------------------------
{% for port in ts.vivado.ports %}
# Set port properties for port "{{port.name}}"
set port [lindex [get_ports {{port.name}}] 0]
set_property IOSTANDARD {{port.iostandard}} $port 
place_port -verbose "$port {{port.package_pin}}"
{% if not loop.last %}

{% endif %}
{% endfor %}
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Post-Synth Optimization 
#------------------------------------------------------------------------------
opt_design
report_timing_summary -file reports/post_opt_timing.rpt
report_utilization -file reports/post_opt_util.rpt
# TODO add more reports? They show example of custom script to report critical paths
# TODO add additional power_opt_design?
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Placement (TODO why is report_clock_utilization done before phys_opt_design?)
#------------------------------------------------------------------------------
place_design
report_clock_utilization -file reports/post_place_clock_util.rpt
# TODO optionally run optimization if there are timing violations after placement
# TODO get phys_opt_Design integrated
#if {[get_property SLACK [get_timing_paths -max_paths 1 -nworst -setup]] < 0} {
#    puts "Found setup timing violations => running physical optimization"
#    phys_opt_design
#}
write_checkpoint -force -verbose checkpoints/post_place.dcp
report_timing_summary -file reports/post_place_timing.rpt
report_utilization -file reports/post_place_util.rpt
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Route
#------------------------------------------------------------------------------
route_design
write_checkpoint -force checkpoints/post_route.dcp
report_route_status -file reports/post_route_status.rpt
report_timing_summary -file reports/post_route_timing.rpt
report_power -file reports/post_route_power.rpt
report_drc -file reports/post_route_drc.rpt
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Final output generation
#------------------------------------------------------------------------------
write_verilog -force -mode timesim -sdf_anno true {{ts.vivado.top}}_post_impl.v
write_bitstream -force -verbose {{ts.vivado.top}}.bit
#------------------------------------------------------------------------------
