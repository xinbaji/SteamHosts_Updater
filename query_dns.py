#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Steam Hosts Updater - DNS查询脚本

该脚本通过DNS查询Steam相关域名的IP地址，并将结果以hosts格式写入文件。

用途：
  - CI/CD 流程中生成hosts文件
  - 本地调试和测试
  - 不需要直接修改系统hosts的场景

注意：此脚本只生成hosts文件，不安装到系统。
      如需直接安装到系统，请使用 SteamHosts_Updater.py
"""

import logging
import socket
import yaml
import urllib.request
import urllib.error
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed


def setup_logging(log_to_file=False):
    """设置日志系统

    Args:
        log_to_file: 是否将日志输出到文件
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if log_to_file:
        # 生成带秒的时间戳的日志文件名
        log_filename = 'query_dns_{}.log'.format(
            datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        log_file = Path.cwd() / log_filename

        # 配置日志同时输出到文件和控制台
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        print("日志文件: {}".format(log_file))
    else:
        # 默认只输出到控制台
        logging.basicConfig(
            level=logging.INFO,
            format=log_format
        )

    return logging.getLogger(__name__)


class DnsQueryError(Exception):
    """DNS查询异常类"""
    pass


def query_dns_api(domain: str, dns_server: str = 'https://dns.google/resolve') -> List[str]:
    """使用Google DNS API查询域名IP地址

    Args:
        domain: 要查询的域名
        dns_server: DNS API地址,默认Google DNS

    Returns:
        IP地址列表
    """
    try:
        url = f"{dns_server}?name={domain}&type=A"
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('Status') != 0:
                raise DnsQueryError(f"DNS查询失败: {data.get('Status')}")

            answers = data.get('Answer', [])
            if not answers:
                raise DnsQueryError(f"未找到域名 {domain} 的DNS记录")

            ips = []
            for answer in answers:
                ip = answer.get('data')
                if ip:
                    ips.append(ip)

            if not ips:
                raise DnsQueryError(f"未找到域名 {domain} 的IP地址")

            return ips

    except urllib.error.URLError as e:
        raise DnsQueryError(f"网络请求失败: {e}")
    except json.JSONDecodeError as e:
        raise DnsQueryError(f"JSON解析失败: {e}")


def test_ip_speed(ip: str, port: int = 80, timeout: int = 5) -> float:
    """测试IP连接速度

    Args:
        ip: IP地址
        port: 端口号
        timeout: 超时时间(秒)

    Returns:
        连接耗时(秒)
    """
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            return time.time() - start_time
        else:
            return float('inf')  # 连接失败
    except socket.error:
        return float('inf')  # 连接异常


def test_ip_speed_single(ip: str, port: int = 80, timeout: int = 5, max_test: int = 3) -> tuple[str, float]:
    """测试单个IP的平均连接速度（用于多线程）

    Args:
        ip: IP地址
        port: 端口号
        timeout: 超时时间(秒)
        max_test: 测试次数

    Returns:
        (ip, 平均速度) 元组
    """
    speeds = []
    for i in range(max_test):
        speed = test_ip_speed(ip, port, timeout)
        if speed != float('inf'):
            speeds.append(speed)

    if speeds:
        avg_speed = sum(speeds) / len(speeds)
        return (ip, avg_speed)
    else:
        return (ip, float('inf'))


def select_fastest_ip(ips: List[str], logger: logging.Logger, max_test: int = 3) -> str:
    """从多个IP中选择连接最快的一个（多线程版本）

    Args:
        ips: IP地址列表
        logger: 日志记录器
        max_test: 每个IP测试的最大次数

    Returns:
        最快的IP地址
    """
    if len(ips) == 1:
        return ips[0]

    logger.info(f"开始多线程测速,共 {len(ips)} 个IP地址")

    ip_speeds = []
    
    # 使用线程池对每个IP并行测速
    with ThreadPoolExecutor(max_workers=len(ips)) as executor:
        # 提交所有IP的测速任务
        future_to_ip = {
            executor.submit(test_ip_speed_single, ip, 80, 5, max_test): ip 
            for ip in ips
        }
        
        # 收集结果
        for future in as_completed(future_to_ip):
            ip, avg_speed = future.result()
            ip_speeds.append((ip, avg_speed))
            
            if avg_speed == float('inf'):
                logger.info(f"  {ip}: 连接失败")
            else:
                logger.info(f"  {ip}: 平均 {avg_speed:.3f}秒")

    # 选择平均速度最快的IP
    ip_speeds.sort(key=lambda x: x[1])
    fastest_ip = ip_speeds[0][0]

    if ip_speeds[0][1] == float('inf'):
        raise DnsQueryError("所有IP地址都无法连接")

    logger.info(f"选择最快IP: {fastest_ip}")
    return fastest_ip


class HostsWriter:
    """Hosts文件写入器"""
    
    def __init__(self, config_path: str = 'config.yaml', log_to_file: bool = False) -> None:
        """初始化写入器

        Args:
            config_path: 配置文件路径
            log_to_file: 是否将日志输出到文件
        """
        config: dict[str, Any] = self._load_config(config_path, None)
        self._setup_logging(config, log_to_file)
        self.logger = logging.getLogger(__name__)
        self.config = config
    
    def _load_config(self, config_path: str, logger: Optional[logging.Logger]) -> dict[str, Any]:
        """加载配置文件

        Args:
            config_path: 配置文件路径
            logger: 日志记录器（可选）

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: 配置文件格式错误
        """
        config_file = Path(config_path)
        if not config_file.exists():
            if logger:
                logger.info(f"配置文件 {config_path} 不存在，使用默认配置")
            # 默认配置
            return {
                'steam_domains': [
                    'store.steampowered.com',
                    'steamcommunity.com',
                    'api.steampowered.com',
                    'steamuserimages-a.akamaihd.net',
                    'steamcdn-a.akamaihd.net',
                    'steamcommunity-a.akamaihd.net',
                    'steamstore-a.akamaihd.net',
                    'steambroadcast.akamaized.net',
                    'steamvideo-a.akamaihd.net',
                    'help.steampowered.com',
                    'support.steampowered.com',
                    'steamgames.com',
                    'steamusercontent.com',
                    'steamcontent.com',
                    'steamstatic.com',
                    'akamaihd.net'
                ],
                'dns': {'server': '8.8.8.8', 'timeout': 5},
                'output': {'hosts_file': 'hosts', 'backup_file': 'hosts.backup'},
                'logging': {'level': 'INFO', 'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}
            }

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if logger:
                    logger.info(f"成功加载配置文件: {config_path}")
                return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"配置文件格式错误: {e}\n"
                f"请检查YAML语法是否正确。"
            )
    
    def _setup_logging(self, config: dict[str, Any], log_to_file=False) -> None:
        """设置日志系统

        Args:
            config: 配置字典
            log_to_file: 是否将日志输出到文件
        """
        log_config = config.get('logging', {})
        log_format = log_config.get(
            'format',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        if log_to_file:
            # 生成带秒的时间戳的日志文件名
            log_filename = 'query_dns_{}.log'.format(
                datetime.now().strftime('%Y%m%d_%H%M%S')
            )
            log_file = Path.cwd() / log_filename

            # 配置日志同时输出到文件和控制台
            logging.basicConfig(
                level=getattr(logging, log_config.get('level', 'INFO')),
                format=log_format,
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            print("日志文件: {}".format(log_file))
        else:
            # 默认只输出到控制台
            logging.basicConfig(
                level=getattr(logging, log_config.get('level', 'INFO')),
                format=log_format
            )
    
    def query_dns(self, domain: str) -> str:
        """查询域名的IP地址
        
        Args:
            domain: 要查询的域名
            
        Returns:
            IP地址字符串
            
        Raises:
            DnsQueryError: DNS查询失败
        """
        dns_server = self.config['dns']['server']
        timeout = self.config['dns']['timeout']
        
        try:
            # 使用指定的DNS服务器进行查询
            resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            resolver.settimeout(timeout)
            resolver.connect((dns_server, 53))
            local_ip = resolver.getsockname()[0]
            resolver.close()
            
            # 实际DNS查询
            ip_address = socket.gethostbyname(domain)
            self.logger.info(f"查询成功: {domain} -> {ip_address}")
            return ip_address
            
        except socket.timeout:
            raise DnsQueryError(
                f"DNS查询超时: {domain}\n"
                f"可能的解决方案:\n"
                f"1. 检查网络连接\n"
                f"2. 确认DNS服务器 {dns_server} 可访问\n"
                f"3. 尝试增加timeout配置值"
            )
        except socket.gaierror as e:
            raise DnsQueryError(
                f"DNS解析失败: {domain}\n"
                f"错误信息: {e}\n"
                f"可能的解决方案:\n"
                f"1. 确认域名拼写正确\n"
                f"2. 检查网络连接\n"
                f"3. 尝试更换DNS服务器"
            )
        except Exception as e:
            raise DnsQueryError(
                f"未知错误: {domain}\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {e}\n"
                f"请联系技术支持并提供完整日志"
            )
    
    def query_all_domains(self) :
        """查询所有域名的IP地址
        
        Returns:
            hosts格式的记录列表
        """
        domains = self.config['steam_domains']
        hosts_entries = []
        
        self.logger.info(f"开始查询 {len(domains)} 个域名...")
        
        for domain in domains:
            try:
                ip = self.query_dns(domain)
                hosts_entries.append(f"{ip}\t{domain}")
            except DnsQueryError as e:
                self.logger.error(str(e))
                # 继续查询其他域名
                continue
        
        self.logger.info(f"成功查询 {len(hosts_entries)}/{len(domains)} 个域名")
        return hosts_entries
    
    def write_hosts_file(self, hosts_entries) -> None:
        """将查询结果写入hosts文件
        
        Args:
            hosts_entries: hosts记录列表
        """
        output_file = Path(self.config['output']['hosts_file'])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成内容
        content = f"""# ============================================
# Steam Hosts - 由程序自动生成
# 生成时间: {now}
# DNS服务器: {self.config['dns']['server']}
# ============================================
"""
        content += "\n".join(hosts_entries)
        content += """\n# ============================================
# Steam Hosts结束
# ============================================
\n"""
        
        # 写入文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"成功写入hosts文件: {output_file}")
        except IOError as e:
            raise IOError(
                f"写入文件失败: {output_file}\n"
                f"错误信息: {e}\n"
                f"可能的解决方案:\n"
                f"1. 检查是否有写入权限\n"
                f"2. 确认磁盘空间充足\n"
                f"3. 检查文件是否被其他程序占用"
            )
    
    def run(self) -> None:
        """执行主流程"""
        try:
            self.logger.info("=" * 50)
            self.logger.info("Steam Hosts更新程序启动")
            self.logger.info("=" * 50)
            
            # 查询所有域名
            hosts_entries = self.query_all_domains()
            
            if not hosts_entries:
                raise DnsQueryError(
                    "没有成功查询到任何域名IP地址。\n"
                    "请检查网络连接和DNS服务器配置。"
                )
            
            # 写入hosts文件
            self.write_hosts_file(hosts_entries)
            
            self.logger.info("=" * 50)
            self.logger.info("Steam Hosts更新完成")
            self.logger.info("=" * 50)
            
        except Exception as e:
            self.logger.error(f"程序执行失败: {e}")
            raise


def main():
    """主函数"""
    try:
        updater = HostsWriter(log_to_file=False)
        updater.run()
    except Exception as e:
        print(f"\n[错误] {e}")
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
