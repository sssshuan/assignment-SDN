# qos With P4Runtime

> 在 [qos](https://github.com/p4lang/tutorials/tree/master/exercises/qos) 实验的基础上，去掉流规则静态下发，实现P4Runtime的动态下发。

#### 步骤1：去掉 topology.json 里交换机的配置

![截屏2022-04-23 下午4.24.51](https://tva1.sinaimg.cn/large/e6c9d24ely1h1jqfj7qdhj20m20c9ab6.jpg)

#### 步骤2：新建 `mycontroller.py`

- 修改路径

![截屏2022-04-24 上午8.31.37](https://tva1.sinaimg.cn/large/e6c9d24ely1h1kidwio55j20ok05bt9o.jpg)

- 写入规则的函数

```c
def writeIpv4Rules(p4info_helper, ingress_sw, dst_eth_addr, egress_port, dst_ip_addr, mask_bits):
    """
    :param p4info_helper: the P4Info helper
    :param ingress_sw: the ingress switch connection
    :param dst_eth_addr: the destination Ethernet address to write in the egress rule
    :param egress_port: 出端口
    :param dst_ip_addr: the destination IP to match in the ingress rule
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

- 具体调用直接看github



#### 步骤3：重新运行

- 运行 `./mycontroller.py` 之前，ping发现主机不互通，说明转发规则没有下发

- 然后在另一终端2运行 `./mycontroller.py`，此时ping发现主机互通

![截屏2022-04-24 上午8.39.41](https://tva1.sinaimg.cn/large/e6c9d24ely1h1kilnmrcjj20o20f1q3z.jpg) 



- 再次在h1上使用send .py每秒发送一个数据包到h2，持续30秒，分成两种情况: TCP和UDP

> 可以看到结果与静态下发一样，h2收到的IP数据包中的tos值发生了变化，如果是UDP流是0xb9，如果是TCP流是0xb1

<center><figure>
    <img src="https://tva1.sinaimg.cn/large/e6c9d24ely1h1kjf65pc1j20dh0itdgo.jpg" alt="截屏2022-04-24 上午8.59.56" style="zoom:70%;" />
    <img src="https://tva1.sinaimg.cn/large/e6c9d24ely1h1kjfkk7vzj20dh0itaaz.jpg" alt="截屏2022-04-24 上午9.00.58" style="zoom:70%;" />
</figure></center>

