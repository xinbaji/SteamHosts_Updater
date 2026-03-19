#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Steam Hosts Updater - 单文件版本"""

import logging
import socket
import yaml
import os
import platform
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import cast

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DnsQueryError(Exception):
    """DNS查询异常类"""
    pass


class HostsInstallError(Exception):
    """Hosts安装异常类"""
    pass


def get_hosts_path():
    """获取系统hosts文件路径"""
    system = platform.system()
    paths = {
        'Windows': r'C:\Windows\System32\drivers\etc\hosts',
        'Darwin': '/etc/hosts',
        'Linux': '/etc/hosts'
    }
    return paths.get(system)


def query_dns(domain, dns_server='8.8.8.8', timeout=5):
    """查询域名IP地址"""
    try:
        ip = socket.gethostbyname(domain)
        logger.info("查询成功: {} -> {}".format(domain, ip))
        return ip
    except socket.gaierror as e:
        raise DnsQueryError("DNS解析失败: {}".format(e))


def query_all_domains(domains):
    """查询所有域名"""
    entries = []
    for domain in domains:
        try:
            ip = query_dns(domain)
            entries.append("{}\t{}".format(ip, domain))
        except DnsQueryError as e:
            logger.error(str(e))
    return entries


def write_hosts_file(entries, output_file='hosts'):
    """写入hosts文件"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    content = "# ============================================\n"
    content += "# Steam Hosts - 由程序自动生成\n"
    content += "# 生成时间: {}\n".format(now)
    content += "# DNS服务器: 8.8.8.8\n"
    content += "# ============================================\n"
    content += "\n".join(entries)
    content += "\n# ============================================\n"
    content += "# Steam Hosts结束\n"
    content += "# ============================================\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("成功写入hosts文件: {}".format(output_file))
    return content


def backup_hosts(hosts_path):
    """备份hosts文件"""
    backup_dir = Path.home() / '.steam_hosts_updater' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / 'hosts_{}.backup'.format(timestamp)
    
    if Path(hosts_path).exists():
        shutil.copy2(hosts_path, backup_file)
        logger.info("已备份hosts文件到: {}".format(backup_file))
    
    return str(backup_file)


def update_system_hosts(hosts_path, steam_hosts_content):
    """更新系统hosts文件"""
    hosts_file = Path(hosts_path)
    
    # 读取现有内容
    existing = ""
    if hosts_file.exists():
        with open(hosts_file, 'r', encoding='utf-8') as f:
            existing = f.read()
    
    # 移除旧的Steam hosts
    lines = existing.split('\n')
    filtered = []
    in_section = False
    for line in lines:
        if 'Steam Hosts - 由程序自动生成' in line:
            in_section = True
        elif 'Steam Hosts结束' in line:
            in_section = False
        elif not in_section:
            filtered.append(line)
    
    # 添加新内容
    new_content = '\n'.join(filtered).strip() + '\n\n' + steam_hosts_content + '\n'
    
    with open(hosts_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    logger.info("成功更新hosts文件: {}".format(hosts_path))


def check_admin():
    """检查管理员权限"""
    if platform.system() == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.access('/etc', os.W_OK)


def flush_dns():
    """刷新DNS缓存"""
    system = platform.system()
    commands = {
        'Windows': ['ipconfig', '/flushdns'],
        'Darwin': ['sudo', 'dscacheutil', '-flushcache'],
        'Linux': ['sudo', 'systemctl', 'restart', 'nscd']
    }
    
    cmd = commands.get(system)
    if cmd:
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            logger.info("DNS缓存刷新成功")
        except:
            logger.warning("DNS刷新失败")


def get_config_path():
    """获取配置文件路径，支持打包后的路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的情况，资源在临时目录（PyInstaller 特有属性）
        # 使用 getattr + default 来绕过类型检查
        base_path = cast(str, getattr(sys, '_MEIPASS', ''))
    else:
        # 正常运行的情况
        base_path = Path(__file__).parent

    config_path = Path(base_path) / 'config.yaml'

    # 如果打包后没有配置文件，检查工作目录
    if getattr(sys, 'frozen', False) and not config_path.exists():
        config_path = Path.cwd() / 'config.yaml'

    return str(config_path)


def update(install=False):
    """执行更新流程"""
    logger.info("=" * 50)
    logger.info("Steam Hosts更新程序启动")
    logger.info("=" * 50)

    # 加载配置
    config_path = get_config_path()
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info("加载配置文件: {}".format(config_path))
    else:
        logger.info("未找到配置文件，使用默认配置")
        # 默认配置
        config = {
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
                'support.steampowered.com'
            ],
            'dns': {'server': '8.8.8.8', 'timeout': 5},
            'output': {'hosts_file': 'hosts'}
        }

    domains = config.get('steam_domains', [])

    # 查询DNS
    entries = query_all_domains(domains)
    if not entries:
        raise DnsQueryError("没有成功查询到任何域名IP地址")

    # 写入hosts文件
    output_config = config.get('output')
    hosts_file = 'hosts'
    if isinstance(output_config, dict):
        file_value = output_config.get('hosts_file')
        if isinstance(file_value, str):
            hosts_file = file_value
    elif isinstance(output_config, str):
        hosts_file = output_config
    steam_hosts_content = write_hosts_file(entries, hosts_file)
    
    # 安装到系统
    if install:
        logger.info("正在安装到系统hosts文件...")
        
        if not check_admin():
            raise HostsInstallError("需要管理员/root权限才能修改系统hosts文件")
        
        hosts_path = get_hosts_path()
        if not hosts_path:
            raise HostsInstallError("不支持的操作系统")
        
        backup_hosts(hosts_path)
        update_system_hosts(hosts_path, steam_hosts_content)
        flush_dns()
    
    logger.info("=" * 50)
    logger.info("Steam Hosts更新完成")
    logger.info("=" * 50)


def main():
    """主函数"""
    import sys

    install = '--install' in sys.argv or '-i' in sys.argv

    try:
        if install:
            update(install=True)
        else:
            print("\n使用方法:")
            print("  python steam_hosts_updater.py         # 仅生成hosts文件")
            print("  python steam_hosts_updater.py -i       # 生成并安装到系统")
            print("  python steam_hosts_updater.py --install # 生成并安装到系统")
            print("")
            update(install=False)
    except Exception as e:
        print("\n[错误] {}".format(e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
