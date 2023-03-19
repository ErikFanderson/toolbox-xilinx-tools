# Start/connect to the hardware server (manages connections to FPGAs)
open_hw_manager
connect_hw_server -url {{ts.upload.hw_server.hostname}}:{{ts.upload.hw_server.port}}

{% if ts.upload.query_targets %}
# Query hardware targets
puts [get_hw_targets]
{% else %}
# Open specified hardware target (target represents JTAG chain of devices)
current_hw_target [get_hw_targets {{ts.upload.target}}]
set_property PARAM.FREQUENCY {{ts.upload.frequency}} [get_hw_targets {{ts.upload.target}}]
open_hw_target

# Associate bitstream and mask file with hardware device (device is Xilinx device)
create_hw_bitstream \
    -hw_device [current_hw_device] \
    -mask {{ts.upload.mask|realpath}} \
    {{ts.upload.bitstream|realpath}}

# Program hardware
program_hw_devices [current_hw_device]
refresh_hw_device [current_hw_device]
verify_hw_devices -verbose [current_hw_device]
{% endif %}
