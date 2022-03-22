

# Basic Forwarding Plus ARP

> 在 [Basic Forwarding](https://github.com/p4lang/tutorials/tree/master/exercises/basic) 实验的基础上，去掉 `topology.json` 里为每台主机定义的arp转发选项，并把arp功能实现到现有的basic.p4中



## 去掉topology.json里的arp转发选项

- 修改前：

![截屏2022-03-22 下午7.20.39](https://tva1.sinaimg.cn/large/e6c9d24ely1h0ivzg6m5rj20ll0d440n.jpg)

- 修改后：

![截屏2022-03-22 下午7.17.18](https://tva1.sinaimg.cn/large/e6c9d24ely1h0ivz1rp8cj20ll0b8gn8.jpg)



- 修改完后，执行 `make run`，可以成功进入mininet，但是ping将会失败，因为任意主机都不知道其他主机的MAC地址

![截屏2022-03-22 下午7.37.09](https://tva1.sinaimg.cn/large/e6c9d24ely1h0iw5wtvvuj20sb09yjsw.jpg)

![截屏2022-03-22 下午7.37.18](https://tva1.sinaimg.cn/large/e6c9d24ely1h0iw7qb06aj20sd05lt8x.jpg)



## 修改basic.p4



1、 需要定义 ARP 报文格式数据结构，并加到 headers 结构体里

> ARP知识可参考  [文章1](https://blog.csdn.net/u011784495/article/details/71716586)    [文章2](https://blog.csdn.net/deramer1/article/details/73467048)

2、定义一些 arp 相关常量

3、用户自定义metadata，用于保存相关数据

4、 修改 MyParser，添加 arp 解析逻辑

> 解析以太网头部，根据以太网头部协议类型，决定进行ipv4 还是 arp解析

5、修改MyIngress，这是最复杂的部分

- 首先，无论 ipv4转发 还是 arp，都需要知道下一跳ip对应的MAC地址，所以跟basic forwarding实验一样，由一个流表进行匹配目的 ip，并给出目的MAC地址和输出端口

  > 代码里的 ipv4_lpm 和 set_dst_info 与该步骤相对应

  注意：**这里还需要对s1-runtime.json,  ... , s4-runtime.json 作修改，从而与流表`ipv4_lpm`相对应。**	

  ![截屏2022-03-22 下午8.10.17](https://tva1.sinaimg.cn/large/e6c9d24ely1h0ix632dtxj20sn0eqgo7.jpg)



- 然后，需要另一个流表`forward`，用于决定是arp响应还是ipv4转发

  这里arp 的处理方法是交换机直接把 ARP请求报文目的IP所对应的目的主机MAC地址 返回给源主机，需要做的有：

  - ARP请求报文的源MAC地址 作为 ARP响应帧目的MAC地址
  - ARP请求报文的目的IP所对应的主机MAC地址 作为 ARP响应帧的源MAC
  - ARP请求报文的源MAC地址 作为 ARP响应报文的目的MAC地址
  - ARP请求报文的源IP 作为 ARP响应报文的目的IP
  - ARP请求报文的目的IP所对应的主机的MAC地址 作为 ARP响应报文的源MAC地址
  - ARP请求报文的目的IP 作为 ARP响应报文的源IP
  - ARP操作类型设置为 REPLY
  - 从哪个端口来的 从哪个端口回去

6、修改MyDeparser，添加重组arp的逻辑



## 重新运行

> 记得先执行`make clean`清除之前的构建

将会ping通

![截屏2022-03-22 下午8.23.32](https://tva1.sinaimg.cn/large/e6c9d24ely1h0ixi5kjp7j20so097q4f.jpg)

![截屏2022-03-22 下午8.22.19](https://tva1.sinaimg.cn/large/e6c9d24ely1h0ixgwi59aj20or05eweo.jpg)

