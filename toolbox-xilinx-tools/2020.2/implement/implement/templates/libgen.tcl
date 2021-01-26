{% extends "base.tcl" %}
{% block description %}
abstract.tcl
{% endblock %}
{% block content %}

#----------------------------------------------------------
# Define templates
#----------------------------------------------------------
define_template -type delay \
    -index_1 { {{input_slew|join(' ')}} } \
    -index_2 { {{output_load|join(' ')}} } \
    delay_template

define_template -type power \
    -index_1 { {{input_slew|join(' ')}} } \
    -index_2 { {{output_load|join(' ')}} } \
    power_template
#----------------------------------------------------------

#----------------------------------------------------------
# Set operating conditions
#----------------------------------------------------------
set_operating_condition -voltage {{ts.liberate.voltage}} -temp {{ts.liberate.temperature}}
#----------------------------------------------------------

{% if ts.liberate.power_nets %}
#----------------------------------------------------------
# Power nets 
#----------------------------------------------------------
{% for net in ts.liberate.power_nets %}
set_vdd {{net.name}} {{net.value}} 
{% endfor %}
#----------------------------------------------------------

{% endif %}
{% if ts.liberate.ground_nets %}
#----------------------------------------------------------
# Ground nets 
#----------------------------------------------------------
{% for net in ts.liberate.ground_nets %}
set_gnd {{net.name}} {{net.value}} 
{% endfor %}
#----------------------------------------------------------

{% endif %}
#----------------------------------------------------------
# Read spice files 
#----------------------------------------------------------
read_spice -format {{ts.liberate.netlist_format}} { {{ts.liberate.spice_files|realpathjoin(' ')}} }
#----------------------------------------------------------

{% if ts.liberate.arcs %}
#----------------------------------------------------------
# User defined arcs
#----------------------------------------------------------
{% for arc in ts.liberate.arcs %}
define_arc -pin {{arc.pin}} -pin_dir {{arc.pin_dir}} -related_pin {{arc.related_pin}} -related_pin_dir {{arc.related_pin_dir}} {{ts.liberate.cell}}
{% endfor %}
#----------------------------------------------------------

{% endif %}
#----------------------------------------------------------
# Define cell to be characterized 
#----------------------------------------------------------
define_cell \
    -input { {{ts.liberate.cell_pins.input|join(' ')}} } \
    -output { {{ts.liberate.cell_pins.output|join(' ')}} } \
    {% if "async" in ts.liberate.cell_pins %}
    -async { {{ts.liberate.cell_pins.async|join(' ')}} } \
    {% endif %}
    {% if "bidi" in ts.liberate.cell_pins %}
    -bidi { {{ts.liberate.cell_pins.bidi|join(' ')}} } \
    {% endif %}
    -pinlist { {{pin_list|join(' ')}} } \
    -delay delay_template \
    -power power_template \
    { {{ts.liberate.cell}} }
#----------------------------------------------------------

#----------------------------------------------------------
# Perform characterization and export .lib
#----------------------------------------------------------
char_library
set_units -capacitance {{ts.liberate.cap_unit}}
set_units -timing {{ts.liberate.time_unit}}
write_library {{lib_name}}.lib
write_datasheet {{lib_name}} 
#----------------------------------------------------------

{% endblock %}
