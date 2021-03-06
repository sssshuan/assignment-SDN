/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> ETHERTYPE_ARP  = 0x0806;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}


//NOTE: ARP format https://blog.csdn.net/u011784495/article/details/71716586
header arp_t {
    bit<16> htype; // format of hardware address
    bit<16> ptype; // format of protocol address
    bit<8>  hlen; // length of hardware address
    bit<8>  plen; // length of protocol address
    bit<16> oper; // request or reply operation
}

header arp_ipv4_t {
    macAddr_t  sha; //src mac address (注意与 以太网帧的MAC地址 作区别)
    ip4Addr_t spa; //src ip address
    macAddr_t  tha; // dst mac address (注意与 以太网帧的MAC地址 作区别)
    ip4Addr_t tpa; // dst ip address
}

const bit<16> ARP_HTYPE_ETHERNET = 0x0001;
const bit<16> ARP_PTYPE_IPV4     = 0x0800;
const bit<8>  ARP_HLEN_ETHERNET  = 6;
const bit<8>  ARP_PLEN_IPV4      = 4;
const bit<16> ARP_OPER_REQUEST   = 1;
const bit<16> ARP_OPER_REPLY     = 2;


// User-Defined metadata
struct metadata {
    ip4Addr_t dst_ipv4; // dst ip
    macAddr_t  mac_da; // dst MAC
    egressSpec_t   egress_port;
}

struct headers {
    ethernet_t   ethernet;
    arp_t arp;
    arp_ipv4_t arp_ipv4;
    ipv4_t       ipv4;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            ETHERTYPE_ARP: parse_arp;
            default: accept;
        }
    }

    state parse_arp {
        packet.extract(hdr.arp);
        transition select(hdr.arp.htype, hdr.arp.ptype,
                          hdr.arp.hlen,  hdr.arp.plen) {
            (ARP_HTYPE_ETHERNET, ARP_PTYPE_IPV4,
             ARP_HLEN_ETHERNET,  ARP_PLEN_IPV4) : parse_arp_ipv4;
            default : accept;
        }
    }

    state parse_arp_ipv4 {
        packet.extract(hdr.arp_ipv4);
        meta.dst_ipv4 = hdr.arp_ipv4.tpa; //存下目的ip
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.dst_ipv4 = hdr.ipv4.dstAddr; //存下目的ip
        transition accept;
    }

}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop(standard_metadata);
    }

	/*
	 * dstAddr: sX-runtime.json里流表规则根据 ARP请求报文的目的IP 匹配成功后所给的 目的主机的MAC地址
	 * port: 输出端口，只对ipv4转发有用
	 */
    action set_dst_info(macAddr_t dstAddr,
                        egressSpec_t  port) {
        meta.mac_da      = dstAddr; 
        meta.egress_port = port;
    }

	/*
	 * ipv4转发
	 */
    action ipv4_forward() {
        standard_metadata.egress_spec = meta.egress_port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = meta.mac_da;
        hdr.ipv4.ttl         = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = { 
        	meta.dst_ipv4 : lpm;
        }
        actions = { 
            set_dst_info;
            drop;  
        }
        size = 1024;
        default_action = drop();
    }

	/*
	 * arp响应，采用的方法是交换机直接把 ARP请求报文目的IP所对应的目的主机MAC地址 返回给源主机
	 */
    action send_arp_reply() {
        hdr.ethernet.dstAddr = hdr.arp_ipv4.sha; // ARP请求报文的源MAC地址 作为 ARP响应帧目的MAC地址
        hdr.ethernet.srcAddr = meta.mac_da; 	 // ARP请求报文的目的IP所对应的主机MAC地址 作为 ARP响应帧的源MAC
        
        hdr.arp.oper         = ARP_OPER_REPLY;
        
        hdr.arp_ipv4.tha     = hdr.arp_ipv4.sha; // ARP请求报文的源MAC地址 作为 ARP响应报文的目的MAC地址
        hdr.arp_ipv4.tpa     = hdr.arp_ipv4.spa; // ARP请求报文的源IP 作为 ARP响应报文的目的IP
        hdr.arp_ipv4.sha     = meta.mac_da;      // ARP请求报文的目的IP所对应的主机的MAC地址 作为 ARP响应报文的源MAC地址
        hdr.arp_ipv4.spa     = meta.dst_ipv4;    // ARP请求报文的目的IP 作为 ARP响应报文的源IP

        standard_metadata.egress_spec = standard_metadata.ingress_port; // 从哪个端口来的 从哪个端口回去
    }

	 
    table forward {
        key = {
            hdr.arp.isValid()      : exact;
            hdr.arp.oper           : ternary;
            hdr.arp_ipv4.isValid() : exact;
            hdr.ipv4.isValid()     : exact;
        }
        actions = {
            ipv4_forward;
            send_arp_reply;
            drop;
        }
        const default_action = drop();
        
		//匹配规则
        const entries = {
            ( true, ARP_OPER_REQUEST, true, false) : send_arp_reply(); //arp响应
            ( false, 		_		, false, true) : ipv4_forward(); // ipv4转发
        }
    }


    apply {
        ipv4_lpm.apply(); // 先根据目的ip匹配，得到目的ip主机的MAC地址（下一跳MAC地址）和 端口
        forward.apply();  // 应用转发流表
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
        update_checksum(
            hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}


/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.arp);
        packet.emit(hdr.arp_ipv4);
        packet.emit(hdr.ipv4);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;

