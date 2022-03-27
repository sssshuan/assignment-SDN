# P4Runtime enhance

> 在 [P4Runtime](https://github.com/p4lang/tutorials/tree/master/exercises/p4runtime) 实验的基础上，继续修改mycontroller.py实现3台主机全部互通，且每条链路可以双向计数



### 第一步：修改`writeTunnelRules`方法

原来的`writeTunnelRules`方法里，隧道转发的出端口固定为`SWITCH_TO_SWITCH_PORT`，也就是端口2。可以这样做是因为拓扑图s1和s2刚好都是通过2端口相连。

现在要实现所有主机相连，需要根据拓扑图设置相应的出端口，所以`writeTunnelRules`需要增加一个参数`egress_port`，并修改转发规则的table_entry，参数port设置为`egress_port`

```python
def writeTunnelRules(p4info_helper, ingress_sw, egress_sw, tunnel_id,
                     dst_eth_addr, dst_ip_addr, egress_port): #修改1
    #....
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.myTunnel_exact",
        match_fields={
            "hdr.myTunnel.dst_id": tunnel_id
        },
        action_name="MyIngress.myTunnel_forward",
        action_params={
            "port": egress_port, #修改2
        })
    ingress_sw.WriteTableEntry(table_entry)
    #....
```



### 第二步：修改`main`方法，加入相关代码完成全部主机互通

- 创建s3和P4Runtime连接

```python
s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s3',
            address='127.0.0.1:50053',
            device_id=2,
            proto_dump_file='logs/s3-p4runtime-requests.txt')
```

- 为s3设置主控端

```python
s3.MasterArbitrationUpdate()
```

- 把p4代码安装进s3

```python
s3.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
```

- 补充h1到h3、h3到h1、h2到h3、h3到h2四个转发规则

```python
		# Write the rules that tunnel traffic from h1 to h3
        writeTunnelRules(p4info_helper, ingress_sw=s1, egress_sw=s3, tunnel_id=300,
                         dst_eth_addr="08:00:00:00:03:33", dst_ip_addr="10.0.3.3",
                        egress_port=3)
        # Write the rules that tunnel traffic from h3 to h1
        writeTunnelRules(p4info_helper, ingress_sw=s3, egress_sw=s1, tunnel_id=400,
                         dst_eth_addr="08:00:00:00:01:11", dst_ip_addr="10.0.1.1",
                         egress_port=2)

        # Write the rules that tunnel traffic from h2 to h3
        writeTunnelRules(p4info_helper, ingress_sw=s2, egress_sw=s3, tunnel_id=500,
                         dst_eth_addr="08:00:00:00:03:33", dst_ip_addr="10.0.3.3",
                         egress_port=3)
        # Write the rules that tunnel traffic from h3 to h2
        writeTunnelRules(p4info_helper, ingress_sw=s3, egress_sw=s2, tunnel_id=600,
                         dst_eth_addr="08:00:00:00:02:22", dst_ip_addr="10.0.2.2",
                         egress_port=3)
```

- 读取s3的table entries

```python
readTableRules(p4info_helper, s3)
```

- 补充相关计数器的输出，补充后如下

```python
# Print the tunnel counters every 2 seconds
        while True:
            sleep(2)
            print('\n----- Reading tunnel counters -----')
            print("------  s1 --> s2 -----")
            printCounter(p4info_helper, s1, "MyIngress.ingressTunnelCounter", 100)
            printCounter(p4info_helper, s2, "MyIngress.egressTunnelCounter", 100)
            print("------  s2 --> s1 -----")
            printCounter(p4info_helper, s2, "MyIngress.ingressTunnelCounter", 200)
            printCounter(p4info_helper, s1, "MyIngress.egressTunnelCounter", 200)
            print("------  s1 --> s3 -----")
            printCounter(p4info_helper, s1, "MyIngress.ingressTunnelCounter", 300)
            printCounter(p4info_helper, s3, "MyIngress.egressTunnelCounter", 300)
            print("------  s3 --> s1 -----")
            printCounter(p4info_helper, s3, "MyIngress.ingressTunnelCounter", 400)
            printCounter(p4info_helper, s1, "MyIngress.egressTunnelCounter", 400)
            print("------  s2 --> s3 -----")
            printCounter(p4info_helper, s2, "MyIngress.ingressTunnelCounter", 500)
            printCounter(p4info_helper, s3, "MyIngress.egressTunnelCounter", 500)
            print("------  s3 --> s2 -----")
            printCounter(p4info_helper, s3, "MyIngress.ingressTunnelCounter", 600)
            printCounter(p4info_helper, s2, "MyIngress.egressTunnelCounter", 600)
```



### 第三步：运行修改后的代码

- 在终端1运行 `.mycontroller.py`，终端2运行`pingall`，结果如图

> 终端1

![截屏2022-03-27 下午8.07.37](https://tva1.sinaimg.cn/large/e6c9d24ely1h0oq55142ej20sl0juact.jpg)



![截屏2022-03-27 下午8.12.06](https://tva1.sinaimg.cn/large/e6c9d24ely1h0oq5bk93jj20sl0juad3.jpg) 

![截屏2022-03-27 下午8.12.48](https://tva1.sinaimg.cn/large/e6c9d24ely1h0oq5hv9flj20rc0b03zy.jpg) 

> 终端2

![截屏2022-03-27 下午8.45.07](https://tva1.sinaimg.cn/large/e6c9d24ely1h0oq7samilj20mf04p74f.jpg) 



- 在终端1运行 `.mycontroller.py`，终端2运行`和 h2 ping h3`，结果如图

> 终端1

![截屏2022-03-27 下午8.47.05](https://tva1.sinaimg.cn/large/e6c9d24ely1h0oqad5ylbj20p70kzgpc.jpg)

> 终端2

![截屏2022-03-27 下午8.48.46](https://tva1.sinaimg.cn/large/e6c9d24ely1h0oqbuqdnnj20oy06t752.jpg)

