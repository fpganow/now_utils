import re
from .common import Entity, Variable

def get_connector_name(in_entity: Entity) -> str:

    print(f'in_entity.port_name: {in_entity.port_name}')
    if "ctrlind" in in_entity.port_name:

        ip_wire_name = 'out_ip_'
        if in_entity.direction == Variable.Direction.IN:
            ip_wire_name = 'in_ip_'

        #print(f'Parsing: {in_wire}')
        result = re.findall(r'ctrlind_(\d{2})_([a-zA-Z0-9_]+)', in_entity.port_name)
        #print(f'result: {result}')
        #var_idx = result[0][0]
        ip_wire_name += result[0][1]
        return f'{ip_wire_name}'.lower()

    # Non control/indicator ports, reset, enable_in, enable_clr, enable_out, Clk40...

    return in_entity.port_name.lower()
