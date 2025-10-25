from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
import requests
from urllib.request import urlopen
import json
import re
import ipaddress

accessKeyId = ""  # 自己的阿里云accessKeyId
accessSecret = ""  # 自己的阿里云accessSecret
domain = "example.com"  # 你的主域名

ipv4_flag = 0  # 是否开启ipv4 ddns解析,1为开启，0为关闭
name1_ipv4 = "*"  # 要进行ipv4 ddns解析的子域名，如有多个，逗号(,)隔开
ipv4_endpoints = [
    'https://api-ipv4.ip.sb/ip',
    'https://ipv4.ip.mir6.com/',
    'https://4.ipw.cn',
]  # IPv4 接口列表，按顺序尝试
ipv4_repetition = 2  # 当所有接口失败后重试的次数，0代表不重试

ipv6_flag = 1  # 是否开启ipv6 ddns解析,1为开启，0为关闭
name1_ipv6 = "*"  # 要进行ipv6 ddns解析的子域名，如有多个，逗号(,)隔开
ipv6_endpoints = [
    'https://api-ipv6.ip.sb/ip',
    'https://ipv6.ip.mir6.com/',
    'https://6.ipw.cn',
]  # IPv6 接口列表，按顺序尝试
ipv6_repetition = 0  # 当所有接口失败后重试的次数，0代表不重试

print("开始解析主域名：%s   ↓↓↓↓↓↓" % domain)                         #www.tianlingzi.top 根据blog.zeruns.tech修改
client = AcsClient(accessKeyId, accessSecret, 'cn-hangzhou')

# 获取公网 IP 的通用函数（按端点顺序尝试，并按重试次数循环）
def get_public_ip(endpoints, version='ipv4', timeout=10, retries=0):
    attempts = retries + 1 if retries >= 0 else 1
    for attempt in range(attempts):
        got = None
        for idx, url in enumerate(endpoints, start=1):
            try:
                data = urlopen(url, timeout=timeout).read()
                if isinstance(data, bytes):
                    text = data.decode('utf-8', errors='ignore').strip()
                else:
                    text = str(data).strip()
            except Exception:
                text = None
            if version == 'ipv4':
                if text:
                    ipv4_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
                    ipv4_addresses = re.findall(ipv4_pattern, text)
                    if ipv4_addresses:
                        candidate = ipv4_addresses[-1]
                    else:
                        candidate = None
                    if candidate:
                        parts = candidate.split('.')
                        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                            got = candidate
                            break
                # 失败切换提示
                if idx < len(endpoints):
                    print(f"获取ipv4失败，使用接口{idx+1}(备用)。")
            else:  # ipv6
                if text:
                    try:
                        ipaddress.IPv6Address(text)
                        got = text
                        break
                    except ipaddress.AddressValueError:
                        pass
                if idx < len(endpoints):
                    print(f"获取ipv6失败，使用接口{idx+1}(备用)。")
        if got:
            return got
        else:
            print(f"接口1、接口2和接口3均获取{version}失败,第{attempt+1}次重试。")
    return None

def update(RecordId, RR, Type, Value):  # 修改域名解析记录
    from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
    request = UpdateDomainRecordRequest()
    request.set_accept_format('json')
    request.set_RecordId(RecordId)
    request.set_RR(RR)
    request.set_Type(Type)
    request.set_Value(Value)
    response = client.do_action_with_exception(request)


def add(DomainName, RR, Type, Value):  # 添加新的域名解析记录
    from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
    request = AddDomainRecordRequest()
    request.set_accept_format('json')
    request.set_DomainName(DomainName)
    request.set_RR(RR)  #www.tianlingzi.top 根据blog.zeruns.tech修改
    request.set_Type(Type)
    request.set_Value(Value)    
    response = client.do_action_with_exception(request)
    

print("\n进行ipv4解析\n")            #www.tianlingzi.top 根据blog.zeruns.tech修改
if ipv4_flag == 1:
    ipv4_flag1 = 1
    ipv4 = get_public_ip(ipv4_endpoints, version='ipv4', timeout=10, retries=ipv4_repetition)
    if ipv4 is None:
        print("获取ipv4失败，停止ipv4解析")
        ipv4_flag1 = 0
    else:
        print("获取ipv4成功：%s" % ipv4)
    
    if ipv4_flag1 == 1:
        words_ipv4 = name1_ipv4.split(",")
        for name_ipv4 in words_ipv4:
            print("正在解析域名：%s.%s" % (name_ipv4,domain))
            request = DescribeSubDomainRecordsRequest()
            request.set_accept_format('json')
            request.set_DomainName(domain)
            request.set_SubDomain(name_ipv4 + '.' + domain)
            request.set_Type("A")
            try:
                response = client.do_action_with_exception(request)  # 获取域名解析记录列表
                ipv4_flag2 = 1
            except:
                ipv4_flag2 = 0
                print("获取域名解析记录列表失败，请检查accessKeyId和accessSecret是否填写正确")
            if ipv4_flag2 == 1:
                domain_list = json.loads(response)  # 将返回的JSON数据转化为Python能识别的
                if domain_list['TotalCount'] == 0:
                    try_ipv4 = False
                    try:
                        add(domain, name_ipv4, "A", ipv4)
                        try_ipv4 = True
                        print("新建域名解析成功")
                    except:
                        if try_ipv4 == False:
                            print("新建域名解析失败，可能存在冲突解析(比如：CNAME、NS)，请自查。")
                elif domain_list['TotalCount'] == 1:
                    if domain_list['DomainRecords']['Record'][0]['Value'].strip() != ipv4.strip():
                        update(domain_list['DomainRecords']['Record'][0]['RecordId'], name_ipv4, "A", ipv4)
                        print("修改域名解析成功")
                    else:  #www.tianlingzi.top 根据blog.zeruns.tech修改
                        print("IPv4地址没变")
                elif domain_list['TotalCount'] > 1:
                    from aliyunsdkalidns.request.v20150109.DeleteSubDomainRecordsRequest import DeleteSubDomainRecordsRequest
                    request = DeleteSubDomainRecordsRequest()
                    request.set_accept_format('json')
                    request.set_DomainName(domain)  #www.tianlingzi.top 根据blog.zeruns.tech修改
                    request.set_RR(name_ipv4)
                    request.set_Type("A") 
                    response = client.do_action_with_exception(request)
                    add(domain, name_ipv4, "A", ipv4)
                    print("修改域名解析成功")
                
                
print("\n进行ipv6解析\n")        #www.tianlingzi.top 根据blog.zeruns.tech修改
if ipv6_flag == 1:
    ipv6_flag1 = 1
    ipv6 = get_public_ip(ipv6_endpoints, version='ipv6', timeout=10, retries=ipv6_repetition)
    if ipv6 is None:
        print("获取ipv6失败，停止ipv6解析")
        ipv6_flag1 = 0
    else:
        print("获取ipv6成功：%s" % ipv6)
    
    if ipv6_flag1 == 1:
        words_ipv6 = name1_ipv6.split(",")
        for name_ipv6 in words_ipv6:
            print("正在解析域名：%s.%s" % (name_ipv6,domain))
            request = DescribeSubDomainRecordsRequest()
            request.set_accept_format('json')
            request.set_DomainName(domain)
            request.set_SubDomain(name_ipv6 + '.' + domain)
            request.set_Type("AAAA")
            try:
                response = client.do_action_with_exception(request)  # 获取域名解析记录列表
                ipv6_flag2 = 1
            except:
                ipv6_flag2 = 0
                print("获取域名解析记录列表失败，请检查accessKeyId和accessSecret是否填写正确")
            if ipv6_flag2 == 1:
                domain_list = json.loads(response)  # 将返回的JSON数据转化为Python能识别的
                if domain_list['TotalCount'] == 0:
                    try_ipv6 = False
                    try:
                        add(domain, name_ipv6, "AAAA", ipv6)
                        try_ipv6 = True
                        print("新建域名解析成功")
                    except:
                        if try_ipv6 == False:
                            print("新建域名解析失败，可能存在冲突解析(比如：CNAME、NS)，请自查。")
                elif domain_list['TotalCount'] == 1:
                    if domain_list['DomainRecords']['Record'][0]['Value'].strip() != ipv6.strip():
                        update(domain_list['DomainRecords']['Record'][0]['RecordId'], name_ipv6, "AAAA", ipv6)
                        print("修改域名解析成功")
                    else:  #www.tianlingzi.top 根据blog.zeruns.tech修改
                        print("IPv6地址没变")
                elif domain_list['TotalCount'] > 1:
                    from aliyunsdkalidns.request.v20150109.DeleteSubDomainRecordsRequest import DeleteSubDomainRecordsRequest
                    request = DeleteSubDomainRecordsRequest()
                    request.set_accept_format('json')
                    request.set_DomainName(domain)
                    request.set_RR(name_ipv6)  #www.tianlingzi.top 根据blog.zeruns.tech修改
                    request.set_Type("AAAA") 
                    response = client.do_action_with_exception(request)
                    add(domain, name_ipv6, "AAAA", ipv6)
                    print("修改域名解析成功")
                    
print("\n")        #www.tianlingzi.top 根据blog.zeruns.tech修改