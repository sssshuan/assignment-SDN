# load_balance With P4Runtime

> 在 [load_balance](https://github.com/p4lang/tutorials/tree/master/exercises/load_balance) 实验的基础上，去掉流规则静态下发，实现P4Runtime的动态下发。



#### 步骤1：去掉 topology.json 里交换机的配置

![截屏2022-04-23 下午4.24.51](https://tva1.sinaimg.cn/large/e6c9d24ely1h1jqfj7qdhj20m20c9ab6.jpg)



#### 步骤2：新建 `mycontroller.py`

-  `P4Info`、`json`文件路径

![截屏2022-04-23 下午4.29.21](https://tva1.sinaimg.cn/large/e6c9d24ely1h1jqkfq6p2j20m204zjsd.jpg)

- 写入规则的函数

```c
def write_ecmp_group_rules(p4info_helper, ingress_sw, dst_ip_addr,
                            ecmp_base, ecmp_max):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ecmp_group",
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, 32)
        },
        action_name="MyIngress.set_ecmp_select",
        action_params={
            "ecmp_base": ecmp_base,
            "ecmp_count": ecmp_max
        })
    ingress_sw.WriteTableEntry(table_entry)


def write_ecmp_nhop_rules(p4info_helper, ingress_sw, ecmp_select, 
                        nex_hop_ip, nex_hop_mac, egress_port):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ecmp_nhop",
        match_fields={
            "meta.ecmp_select": ecmp_select
        },
        action_name="MyIngress.set_nhop",
        action_params={
            "nhop_dmac": nex_hop_mac,
            "nhop_ipv4": nex_hop_ip,
            "port" : egress_port
        })
    ingress_sw.WriteTableEntry(table_entry)


def write_send_frame_rules(p4info_helper, ingress_sw, egress_port, smac):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyEgress.send_frame",
        match_fields={
            "standard_metadata.egress_port": egress_port
        },
        action_name="MyEgress.rewrite_mac",
        action_params={
            "smac": smac
        })
    ingress_sw.WriteTableEntry(table_entry)
```

- 在main函数里的相关调用

```c
 # Write the rules 
        write_ecmp_group_rules(p4info_helper, ingress_sw=s1, dst_ip_addr="10.0.0.1",
                                 ecmp_base=0, ecmp_max=2)
        write_ecmp_group_rules(p4info_helper, ingress_sw=s2, dst_ip_addr="10.0.2.2",
                                 ecmp_base=0, ecmp_max=1)
        write_ecmp_group_rules(p4info_helper, ingress_sw=s3, dst_ip_addr="10.0.3.3",
                                 ecmp_base=0, ecmp_max=1)

        write_ecmp_nhop_rules(p4info_helper, s1, ecmp_select=0, nex_hop_ip="10.0.2.2", 
                             nex_hop_mac="00:00:00:00:01:02", egress_port=2)
        write_ecmp_nhop_rules(p4info_helper, s1, ecmp_select=1, nex_hop_ip="10.0.3.3", 
                             nex_hop_mac="00:00:00:00:01:03", egress_port=3)
        write_ecmp_nhop_rules(p4info_helper, s2, ecmp_select=0, nex_hop_ip="10.0.2.2", 
                             nex_hop_mac="08:00:00:00:02:02", egress_port=1)
        write_ecmp_nhop_rules(p4info_helper, s3, ecmp_select=0, nex_hop_ip="10.0.3.3", 
                             nex_hop_mac="08:00:00:00:03:03", egress_port=1)

        write_send_frame_rules(p4info_helper, s1, egress_port=2, smac="00:00:00:01:02:00")
        write_send_frame_rules(p4info_helper, s1, egress_port=3, smac="00:00:00:01:03:00")
        write_send_frame_rules(p4info_helper, s2, egress_port=1, smac="00:00:00:02:01:00")
        write_send_frame_rules(p4info_helper, s3, egress_port=1, smac="00:00:00:03:01:00")
```



#### 步骤3：重新运行

- 运行 `./mycontroller.py` 之前，h1发送的消息不会被收到

![截屏2022-04-23 下午6.02.21](https://tva1.sinaimg.cn/large/e6c9d24ely1h1jt9d4hafj20wh0lctaq.jpg)

- 运行 `./mycontroller.py`

![截屏2022-04-23 下午5.58.35](https://tva1.sinaimg.cn/large/e6c9d24ely1h1jt4uxqn1j20t50guwgo.jpg)

- 然后再发送消息，结果同静态下发一样，h1发送的消息有些被`h2`收到有些被`h3`收到

![截屏2022-04-23 下午6.03.50](https://tva1.sinaimg.cn/large/e6c9d24ely1h1jtapblw6j20wh0lcq6b.jpg)

