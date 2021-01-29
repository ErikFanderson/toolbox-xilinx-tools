# Start/connect to the hardware server (manages connections to FPGAs)
open_hw_manager
connect_hw_server -url {{ts.upload.hw_server.hostname}}:{{ts.upload.hw_server.port}}

{% if ts.upload.query_targets %}
# Query hardware targets
puts [get_hw_targets]
{% else %}
# Open specified hardware target 
current_hw_target [get_hw_targets {{ts.upload.target}}]
set_property PARAM.FREQUENCY 15000000 [get_hw_targets {{ts.upload.target}}]
open_hw_target

# Associate bitsream with hardware
set_property PROGRAM.FILE { {{ts.upload.bitstream|realpath}} } [lindex [get_hw_devices] 0]

# Program hardware 
program_hw_devices [lindex [get_hw_devices] 0]
refresh_hw_device [lindex [get_hw_devices] 0]
{% endif %}
