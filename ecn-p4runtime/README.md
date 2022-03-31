# Ecn With P4Runtime

> 在 [ecn](https://github.com/p4lang/tutorials/tree/master/exercises/ecn) 实验的基础上，去掉流规则静态下发，实现P4Runtime的动态下发。



## 步骤1：去掉 topology.json 里交换机的配置

>  sX-runtime.json 文件也可以删除了

![截屏2022-03-30 下午11.08.34](https://tva1.sinaimg.cn/large/e6c9d24ely1h0sb8mc5lkj20tk0ctmyx.jpg)



`pingall` 发现主机不互通

![截屏2022-03-30 下午11.55.59](https://tva1.sinaimg.cn/large/e6c9d24ely1h0sclato3hj20si08vq3e.jpg)



## 步骤2：新建 `mycontroller.py`

> 实现动态下发流规则

- 修改 `P4Info`、`json`文件路径

![截屏2022-03-31 下午8.16.25](https://tva1.sinaimg.cn/large/e6c9d24ely1h0tbw3sr2vj20nj05ydgh.jpg) 

- 下发 ipv4 转发规则

```python
def writeIpv4Rules(p4info_helper, ingress_sw, dst_eth_addr, egress_port, dst_ip_addr, mask_bits):
    """
    写入流规则
    :param p4info_helper: the P4Info helper
    :param ingress_sw: 要写入规则的交换机
    :param dst_eth_addr: 下一跳MAC地址
    :param egress_port: 出端口
    :param dst_ip_addr: 目的ip
    :param mask_bits: 掩码位数
    """
    # ipv4 forward Rule
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
```

> 根据原先 sX-runtime.json里的规则，进行相应的配置（比如下图是s1-runtime.json的内容，`write_s1_rules`写入相同作用的规则）

![截屏2022-03-31 下午3.45.46](https://tva1.sinaimg.cn/large/e6c9d24ely1h0tbho408vj20kw0g60ux.jpg) 

```python
def write_s1_rules(p4info_helper, ingress_sw):
    # s1 -> h1
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:01", egress_port=2,
                   dst_ip_addr="10.0.1.1", mask_bits=32)
    # s1 -> h11
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:11", egress_port=1,
                   dst_ip_addr="10.0.1.11", mask_bits=32)
    # s1 -> s2
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:00", egress_port=3,
                   dst_ip_addr="10.0.2.0", mask_bits=24)
    # s1 -> s3
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:03:00", egress_port=4,
                   dst_ip_addr="10.0.3.0", mask_bits=24)


def write_s2_rules(p4info_helper, ingress_sw):
    # s2 -> h2
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:02", egress_port=2,
                   dst_ip_addr="10.0.2.2", mask_bits=32)
    # s2 -> h22
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:22", egress_port=1,
                   dst_ip_addr="10.0.2.22", mask_bits=32)
    # s2 -> s1
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:00", egress_port=3,
                   dst_ip_addr="10.0.1.0", mask_bits=24)
    # s2 -> s3
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:03:00", egress_port=4,
                   dst_ip_addr="10.0.3.0", mask_bits=24)


def write_s3_rules(p4info_helper, ingress_sw):
    # s3 -> h3
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:03:03", egress_port=1,
                   dst_ip_addr="10.0.3.3", mask_bits=32)
    # s3 -> s1
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:01:00", egress_port=2,
                   dst_ip_addr="10.0.1.0", mask_bits=24)
    # s3 -> s2
    writeIpv4Rules(p4info_helper, ingress_sw=ingress_sw, dst_eth_addr="08:00:00:00:02:00", egress_port=3,
                   dst_ip_addr="10.0.2.0", mask_bits=24)
```

这里需要注意的是，有的lpm掩码是只有24位，如果像之前P4Runtime那样全用32位，会导致一个主机无法发送数据到另一子网的主机。

```python
# 在 main(p4info_file_path, bmv2_file_path)) 里增加这三句
		write_s1_rules(p4info_helper, s1)
        write_s2_rules(p4info_helper, s2)
        write_s3_rules(p4info_helper, s3)
```



## 步骤3：重新运行

- 先打开一个终端1 重新`make run`，然后在另一终端2运行 `./mycontroller.py`

> `./mycontroller.py`结果

![截屏2022-03-31 下午7.49.38](https://tva1.sinaimg.cn/large/e6c9d24ely1h0tbl5o7ipj20rh0jxdia.jpg)

> 终端1 运行 `pingall`，发现主机全部互通

![截屏2022-03-31 下午3.35.26](https://tva1.sinaimg.cn/large/e6c9d24ely1h0tbmd74w4j20l108ft96.jpg) 



