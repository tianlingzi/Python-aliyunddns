# 阿里云 DDNS 脚本（IPv4/IPv6）

一个基于阿里云解析（AliDNS）API 的动态域名解析脚本，自动获取本机公网 IP 并为指定主域名的子域名创建/更新解析记录。支持 IPv4 与 IPv6，内置多接口顺序尝试与超时控制，可配置重试次数。
参考：[zeruns/-Python-aliddns_ipv4-ipv6](https://github.com/zeruns/-Python-aliddns_ipv4-ipv6)

## 运行环境与依赖
- Python `3.7+`
- 依赖库（必须）：
  - `aliyun-python-sdk-core-v3`
  - `aliyun-python-sdk-alidns`
- 可选库：`requests`（当前脚本未强制使用）

安装示例：
- Windows: `pip install aliyun-python-sdk-core-v3 aliyun-python-sdk-alidns`
- Linux: `pip3 install aliyun-python-sdk-core-v3 aliyun-python-sdk-alidns`

## 文件说明
- 脚本文件：`aliyunddns.py`
- 配置项在脚本顶部，使用前需要按下文修改。

## 配置步骤
编辑 `aliyunddns.py` 并设置以下变量：
- `accessKeyId`、`accessSecret`：阿里云访问密钥（建议使用具备最小权限的 RAM 用户密钥）。
- `domain`：你的主域名，例如：`example.com`。
- `ipv4_flag`、`ipv6_flag`：是否开启对应协议的 DDNS（`1` 开启，`0` 关闭）。
- `name1_ipv4`、`name1_ipv6`：需要解析的子域名，多个用逗号分隔；`"*"` 代表泛域名。例如：`"www,home"`。
- `ipv4_endpoints`、`ipv6_endpoints`：获取公网 IP 的接口列表，脚本按序逐个尝试，可自由增删。
- `ipv4_repetition`、`ipv6_repetition`：当所有接口都失败时的重试次数（`0` 表示不重试）。

示例（节选）：
```python
accessKeyId = ""  # 阿里云 accessKeyId
accessSecret = ""  # 阿里云 accessSecret
domain = "example.com"  # 主域名

ipv4_flag = 0
name1_ipv4 = "*"
ipv4_endpoints = [
    'https://api-ipv4.ip.sb/ip',
    'https://ipv4.ip.mir6.com/',
    'https://4.ipw.cn',
]
ipv4_repetition = 2

ipv6_flag = 1
name1_ipv6 = "*"
ipv6_endpoints = [
    'https://api-ipv6.ip.sb/ip',
    'https://ipv6.ip.mir6.com/',
    'https://6.ipw.cn',
]
ipv6_repetition = 0
```

## 工作原理
- 脚本通过通用函数 `get_public_ip(endpoints, version, timeout, retries)` 逐个接口获取公网 IP：
  - IPv4：使用正则与区间校验过滤合法地址。
  - IPv6：使用 `ipaddress.IPv6Address` 校验合法性。
  - 每个接口请求使用 `urlopen(..., timeout=10)`，避免卡住；失败会自动切换到下一个接口；三者都失败后根据重试次数进行循环。
- 获取到 IP 后，调用 AliDNS API 管理解析记录：
  - 使用 `DescribeSubDomainRecordsRequest` 查询现有记录。
  - 无记录：`AddDomainRecordRequest` 新建。
  - 有一条且值不同：`UpdateDomainRecordRequest` 修改。
  - 多条记录：`DeleteSubDomainRecordsRequest` 清理子域名后再新建。
- 记录类型：IPv4 使用 `A`，IPv6 使用 `AAAA`。

## 使用方法
- Windows（在脚本目录）：
  - 运行：`python aliyunddns.py`
- Linux：
  - 运行：`python3 /path/to/aliyunddns.py`
  - 如你将脚本重命名为 `aliddns.py`，运行时请替换对应路径与文件名。

## 多子域名示例
- 同时解析多个子域名：
  - `name1_ipv4 = "www,home,@"`
  - `name1_ipv6 = "nas,router"`
- `@` 代表根记录（即主域名本身）。

## 定时任务示例
- Windows 任务计划程序：创建“基本任务”，触发器选择每 5 分钟，操作选择“启动程序”，程序为 `python`，参数填写脚本路径如 `d:\vscode\aliyunddns\aliyunddns.py`。
- Linux `crontab`：
  - `crontab -e`，添加：
    - `*/5 * * * * /usr/bin/python3 /path/to/aliyunddns.py >> /var/log/aliyunddns.log 2>&1`

## 常见问题
- `NameError: name 'get_public_ip' is not defined`：
  - 请确认你使用的是最新版脚本，且未在调用前删除或移动该函数定义。
- 获取接口卡住不切换：
  - 脚本已对所有接口设置 `timeout`，你可按需调整 `timeout` 值（默认 10 秒）。
- 解析失败或权限报错：
  - 确认 `accessKeyId/accessSecret` 正确，RAM 用户具备 AliDNS 相关权限（建议最小权限）。
- IPv6 无法获取：
  - 确认设备具有公网 IPv6，或替换/增加 `ipv6_endpoints`。

## 安全建议
- 使用具备最小权限的 RAM 用户密钥，限制到 `alidns` 相关操作。
- 不要把密钥硬编码在公开仓库；本地私有使用请注意权限控制。


