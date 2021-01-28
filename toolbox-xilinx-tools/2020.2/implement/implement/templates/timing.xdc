#------------------------------------------------------------------------------
# Set Units (redefine units in every XDC because paranoia)
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
# Clock constraints 
#------------------------------------------------------------------------------
{% for clk in clocks %}
create_clock -verbose -period {{clk.period}} [get_ports {{clk.name}}]
{% endfor %}
#------------------------------------------------------------------------------
