#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
from time import sleep

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 'utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper


def write_check_port_rule(p4info_helper, ingress_sw, ingress_port, egress_port, direction):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.check_ports",
        match_fields={
            "standard_metadata.ingress_port": ingress_port,
            "standard_metadata.egress_spec": egress_port 
        },
        action_name="MyIngress.set_direction",
        action_params={
            "dir": direction
        })
    ingress_sw.WriteTableEntry(table_entry)
    print("Installed check_ports Rule on %s" % ingress_sw.name)

def writeIpv4Rules(p4info_helper, ingress_sw, dst_eth_addr, egress_port, dst_ip_addr, mask_bits):
    """
    
    :param p4info_helper: the P4Info helper
    :param ingress_sw: the ingress switch connection
    :param dst_eth_addr: the destination Ethernet address to write in the egress rule
    :param egress_port: 出端口
    :param dst_ip_addr: the destination IP to match in the ingress rule
    :param mask_bits: 掩码位数
    """
    # 1) ipv4 forward Rule
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ipv4_lpm",
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, mask_bits)
        },
        action_name="MyIngress.ipv4_forward",
        action_params={
            "dstAddr": dst_eth_addr,
            "port": egress_port
        })
    ingress_sw.WriteTableEntry(table_entry)
    print("Installed ipv4 forward Rule on %s" % ingress_sw.name)


def readTableRules(p4info_helper, sw):
    """
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    """
    print('\n----- Reading tables rules for %s -----' % sw.name)
    for response in sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            
            table_name = p4info_helper.get_name("tables", entry.table_id);
            print("table_name: %s" % table_name)

            for m in entry.match:
                print("match: ", end="")
                print(p4info_helper.get_match_field_name(table_name, m.field_id), end="")
                print(" ==  %r" % (p4info_helper.get_match_field_value(m),))
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print('action_name: %s' % action_name)
            for p in action.params:
                print('    param: %s' % p4info_helper.get_action_param_name(action_name, p.param_id), end="")
                print("  %r" % (p.value,))

            print('-----')


def write_s1_rules(p4info_helper, ingress_sw):
    # inner -> outer
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=1, egress_port=3,direction=0)
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=1, egress_port=4,direction=0)
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=2, egress_port=3,direction=0)
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=2, egress_port=4,direction=0)
    # outer -> inner
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=3, egress_port=1,direction=1)
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=3, egress_port=2,direction=1)
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=4, egress_port=1,direction=1)
    write_check_port_rule(p4info_helper, ingress_sw=ingress_sw, ingress_port=4, egress_port=2,direction=1)
    # s1 -> h1
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:11", egress_port=1,
                   dst_ip_addr="10.0.1.1", mask_bits=32)
    # s1 -> h2
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:22", egress_port=2,
                   dst_ip_addr="10.0.2.2", mask_bits=32)
    # s1 -> s3
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:03:00", egress_port=3,
                   dst_ip_addr="10.0.3.3", mask_bits=32)
    # s1 -> s4
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:04:00", egress_port=4,
                   dst_ip_addr="10.0.4.4", mask_bits=32)


def write_s2_rules(p4info_helper, ingress_sw):
    # s2 -> s3
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:03:00", egress_port=4,
                   dst_ip_addr="10.0.1.1", mask_bits=32)
    # s2 -> s4
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:04:00", egress_port=3,
                   dst_ip_addr="10.0.2.2", mask_bits=32)
    # s2 -> h3
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:03:33", egress_port=1,
                   dst_ip_addr="10.0.3.3", mask_bits=32)
    # s2 -> h4
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:04:44", egress_port=2,
                   dst_ip_addr="10.0.4.4", mask_bits=32)


def write_s3_rules(p4info_helper, ingress_sw):
    # s3 -> s1
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:00", egress_port=1,
                   dst_ip_addr="10.0.1.1", mask_bits=32)
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:00", egress_port=1,
                   dst_ip_addr="10.0.2.2", mask_bits=32)
    # s3 -> s2
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:00", egress_port=2,
                   dst_ip_addr="10.0.3.3", mask_bits=32)
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:00", egress_port=2,
                   dst_ip_addr="10.0.4.4", mask_bits=32)

def write_s4_rules(p4info_helper, ingress_sw):
    # s4 -> s1
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:00", egress_port=2,
                   dst_ip_addr="10.0.1.1", mask_bits=32)
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:00", egress_port=2,
                   dst_ip_addr="10.0.2.2", mask_bits=32)
    # s4 -> s2
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:00", egress_port=1,
                   dst_ip_addr="10.0.3.3", mask_bits=32)
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:00", egress_port=1,
                   dst_ip_addr="10.0.4.4", mask_bits=32)

def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create a switch connection object for s1 and s2;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
            proto_dump_file='logs/s1-p4runtime-requests.txt')
        s2 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s2',
            address='127.0.0.1:50052',
            device_id=1,
            proto_dump_file='logs/s2-p4runtime-requests.txt')

        s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s3',
            address='127.0.0.1:50053',
            device_id=2,
            proto_dump_file='logs/s3-p4runtime-requests.txt')
        s4 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s4',
            address='127.0.0.1:50054',
            device_id=3,
            proto_dump_file='logs/s4-p4runtime-requests.txt')

        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        s1.MasterArbitrationUpdate()
        s2.MasterArbitrationUpdate()
        s3.MasterArbitrationUpdate()
        s4.MasterArbitrationUpdate()

        # Install the P4 program on the switches
        s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s1")
        s2.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s2")
        s3.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s3")
        s4.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s4")
        # write table entries to s1 s2 and s3
        write_s1_rules(p4info_helper, s1)
        write_s2_rules(p4info_helper, s2)
        write_s3_rules(p4info_helper, s3)
        write_s4_rules(p4info_helper, s4)
        # read table entries from s1 s2 and s3
        readTableRules(p4info_helper, s1)
        readTableRules(p4info_helper, s2)
        readTableRules(p4info_helper, s3)
        readTableRules(p4info_helper, s4)

        print("successfully completed!")

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/firewall.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/firewall.json')

    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)
    main(args.p4info, args.bmv2_json)
