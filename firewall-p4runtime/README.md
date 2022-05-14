# firewall with p4runtime

> 在 [firewall](https://github.com/p4lang/tutorials/tree/master/exercises/firewall)实验的基础上，去掉流规则静态下发，实现P4Runtime的动态下发。

#### 步骤**1**:去掉 **topology.json** 里交换机的配置

```json
"switches": {
        "s1": { },
        "s2": { },
        "s3": { },
        "s4": { }
    },
```

#### 步骤**2**:新建 **mycontroller.py**

由于与之前实验的动态下发规则原理都差不多，不再赘述，直接见代码链接。

#### 步骤**3**:重新运行

- 运行 `./mycontroller.py` 之前，iperf 的包转发失败，此时，不管是内网主机间通信，还是内网主机主动与外网主机通信，还是外网主机主动与内网主机通信，都无法正常工作（因为没有转发规则）

![截屏2022-05-14 下午12.32.30](https://tva1.sinaimg.cn/large/e6c9d24ely1h27tqnzh88j219w0ckmy3.jpg)

- 运行 `./mycontroller.py` 之后，防火墙功能正常
  - h1往h2是内网间通信，可以正常工作
  - h1往h4发是内网主动与外网通信，可以正常工作
  - h4往h1发是外网主动与内网通信，不允许，数据包会被丢弃。

![截屏2022-05-14 下午12.32.38](https://tva1.sinaimg.cn/large/e6c9d24ely1h27tqs4s4rj219w0g8dhq.jpg)

