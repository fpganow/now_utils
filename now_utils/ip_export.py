import argparse
from datetime import datetime
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, Tuple

from .common import Entity, Variable
from .util import get_connector_name


def get_gen_header(file_name: str) -> str:
    # Check if file_name
    module_name = file_name
    if '.' in file_name:
        module_name = file_name.split('.')[0]
    date_str = datetime.now().strftime("%m/%d/%Y %I:%M %p")

    return f"""\
`timescale 1ns / 1ps

`include "pysv_pkg.sv"
import pysv::*;

//////////////////////////////////////////////////////////////////////////////////
//
// Create Date: {date_str}
// Module Name: {module_name}
// Description: 
//
//
//////////////////////////////////////////////////////////////////////////////////

module {module_name}();

    // 10ns = 100 MHz
    // 20ns = 50 MHz
    // 25ns = 40MHz
    // duration for each bit = 20 * timescale = 20 * 1 ns = 20 ns
    localparam period = 25;
    localparam duty_cycle = period / 2;

    reg clk40;

    always
    begin
        clk40 = 1'b1;
        #duty_cycle;

        clk40 = 1'b0;
        #duty_cycle;
    end
"""


def get_gen_body() -> str:
    return """\
    initial
    begin
        // Set default control signal values
        reset = 0;
        enable_in = 0;
        enable_clr = 0;

        // Reset IP - Hold for 2 clock cycles
        reset = 1;
        #(period * 20);
        $display("Reset IP");

        // Enable IP - Wait for 4 clock cycles
        enable_in = 1;
        reset = 0;
        #(period * 40);

        // Enable IP - Wait for 2 clock cycles
        enable_in = 1;
        #(period*20);

        $display("+=============================================================================+");
        $display("| Start of Tests ");
        $display("+-----------------------------------------------------------------------------+");

        // Test #1 - <description>
        $display("  Test #1 - <description>");

"""


def get_gen_tail() -> str:
    return f"""\
        $display("+-----------------------------------------------------------------------------+");
        $display("| End of TEST BENCH                                                           |");
        $display("+=============================================================================+");
        $display("

        $finish;
    end
endmodule

// AUTO_GENERATED_CODE_END: {__file__.split('/')[-1]}
"""

def parse_entities(vhdl_src: str) -> Tuple[str, Dict[str, Entity]]:
    entity_dict = {}
    target_entity = None

    reading = False
    for line in vhdl_src.split('\n'):
        if line.startswith(f'entity'):
            target_entity = line.split(' ')[1]
            reading = True
        elif line.startswith(f'end {target_entity};'):
            break
        elif reading is True:
            trim_line = line.strip()
            # Ignore non-variable lines
            if trim_line.startswith('port (') or trim_line.startswith(');'):
                pass
            else:
                entity_obj = Entity()
                #print(f'Parsing variable info from:\n\t{trim_line}')
                # Variable Name
                port_name, port_type = trim_line.split(':')
                entity_obj.port_name = port_name.strip()

                # Variable Type
                if 'in ' in port_type:
                    entity_obj.direction = Variable.Direction.IN
                else:
                    entity_obj.direction = Variable.Direction.OUT

                # Variable Type
                if 'std_logic_vector' in port_type:
                    result = re.search('.*\((.*)\);', port_type)
                    first_bound, type_str, second_bound =  result.group(1).split(' ')

                    entity_obj.var_type = Variable.Type.VECTOR

                    if  'to' == type_str:
                        entity_obj.vector_type = Variable.VectorType.ASCENDING
                        entity_obj.vector_size = int(second_bound) - int(first_bound) + 1
                    elif 'downto' == type_str:
                        entity_obj.vector_type = Variable.VectorType.DESCENDING
                        entity_obj.vector_size = int(first_bound) - int(second_bound) + 1
                else:
                    entity_obj.var_type = Variable.Type.SCALAR
                entity_obj.name = get_connector_name(entity_obj)

                entity_dict[port_name] = entity_obj
                #print(f'{entity_obj}')

    return (target_entity, entity_dict)


def parse_args() -> Any:
    parser = argparse.ArgumentParser(
        prog="IP_Export",
        description="Tool to auto-generate verilog stubs for LabVIEW FPGA IP Exported IP"
    )
    parser.add_argument(
        "-v", "--verbose", default=False, action="store_true", help="Verbose"
    )
    parser.add_argument(
        "-d", "--debug", default=False, action="store_true", help="Debug"
    )
    parser.add_argument(
        "-s", "--source", default=None, action="store", type=str, help="Top-Level VHDL file generated by IP Export"
    )
    parser.add_argument(
        "-o", "--output-file", default="autogenerated_tb.v", help="Specify output file (Testbench file name)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Select source VHDL file
    vhdl_src = None
    if args.source is not None:
        vhdl_src = args.source
    else:
        print(f'Source VHDL file not specifed')
        print(f'  - Use -s/--source <vhdl file> to manually specify')
        print(f'  - Checking current directory...')
        pos_files = [x for x in Path('.').glob('NiFpga*.vhd')]
        if len(pos_files) == 1:
            print(f'  - Using {pos_files[0]}')
            vhdl_src = pos_files[0]
        elif len(pos_files) == 0:
            print(f'  - No files matched.  Run in directory where:')
            print(f'    - NiFpgaIPWrapper_???.vhd')
            print(f'    - NiFpgaAG_???.dcp')
            print(f'    (Check C:\\NIFPGA\\compilation)')
            sys.exit(1)
        else:
            print(f'  - More than one file matched, please run again with')
            print(f'    the -s/--source <vhdl file> parameter.')
            print(f'  - FYI, files that matched')
            print('    - ' + '    - '.join([ str(x) + '\n' for x in pos_files]))
            sys.exit(1)

    out_file_name = args.output_file

    print(f'Parsing {vhdl_src} VHDL file.')
    print(f'Output will be saved to {out_file_name}.')

    tab_stop = '    '
    if not Path(vhdl_src).exists():
        print(f'File {vhdl_src} not found')
        sys.exit(1)

    (target_entity, entity_dict) = parse_entities(Path(vhdl_src).read_text())

    print(f'Detected the following ports:')
    for key, val in entity_dict.items():
        print(f'  - {key}')

    out_str = ''
    # File Header
    out_str += get_gen_header(out_file_name)

    # Generate code for instantiating this ip
    # First reg/wire declarations
    #  - reg for input
    #  - wire for output
    out_str += f'    // Variables for {target_entity}\n'
    for key, val in entity_dict.items():
        line_str = "    "
        if val.direction == Variable.Direction.IN:
            line_str += "reg    "
        elif val.direction == Variable.Direction.OUT:
            line_str += "wire   "
        if val.var_type == Variable.Type.VECTOR:
            line_str += f'[{val.vector_size-1:2}:0] '
        else:
            line_str += ' ' * 7
        line_str += f'   {val.name};'

        out_str += f'{line_str}\n'

    # Then UUT and wire it up
    out_str += '\n'
    out_str += f'{tab_stop}{target_entity} UUT (\n'
    # key is port/signal name
    for idx, (key, val) in enumerate(entity_dict.items()):
        tail = ','
        if idx + 1 == len(entity_dict.items()):
            tail = ''
        out_str += f'{tab_stop*2}.{val.port_name}({val.name}){tail}\n'
    out_str += f'{tab_stop});\n\n'

    out_str += get_gen_body()

    out_str += get_gen_tail()

    print('------------------------------------------------------------------------------')
    print(f' Generated file: {out_file_name}')
    print('------------------------------------------------------------------------------')
    print(f'{out_str}')

    print(f'Saving to {out_file_name}')
    Path(out_file_name).write_text(out_str)

if __file__ == "__main__":
    main()
