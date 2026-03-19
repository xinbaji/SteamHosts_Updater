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
import re
from pathlib import Path
from datetime import datetime
from typing import cast

def setup_logging(log_to_file=False):
    """设置日志系统

    Args:
        log_to_file: 是否将日志输出到文件
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if log_to_file:
        # 生成带秒的时间戳的日志文件名
        log_filename = 'steam_hosts_updater_{}.log'.format(
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


# 初始化日志系统（默认不输出到文件）
logger = setup_logging(log_to_file=False)


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


def extract_timestamp(content):
    """从hosts内容中提取生成时间"""
    match = re.search(r'# 生成时间: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
    return datetime.min


def update_system_hosts(hosts_path, steam_hosts_content):
    """更新系统hosts文件，只保留最新的本程序生成内容"""
    hosts_file = Path(hosts_path)
    
    # 读取现有内容
    existing = ""
    if hosts_file.exists():
        with open(hosts_file, 'r', encoding='utf-8') as f:
            existing = f.read()
    
    # 分割为多个本程序生成的内容块
    lines = existing.split('\n')
    sections = []
    current_section = []
    in_section = False
    current_timestamp = datetime.min
    
    for line in lines:
        if 'Steam Hosts - 由程序自动生成' in line:
            # 遇到新段落，保存旧段落
            if in_section and current_section:
                timestamp = extract_timestamp('\n'.join(current_section))
                sections.append({
                    'timestamp': timestamp,
                    'content': current_section
                })
            # 开始新段落
            in_section = True
            current_section = [line]
        elif 'Steam Hosts结束' in line:
            current_section.append(line)
            in_section = False
            # 保存这个段落
            timestamp = extract_timestamp('\n'.join(current_section))
            sections.append({
                'timestamp': timestamp,
                'content': current_section
            })
            current_section = []
        elif not in_section:
            # 非本程序生成的行
            sections.append({
                'timestamp': datetime.max,  # 系统原有内容，永不删除
                'content': [line]
            })
        else:
            current_section.append(line)
    
    # 如果还在段落内（文件未正确结束）
    if in_section and current_section:
        timestamp = extract_timestamp('\n'.join(current_section))
        sections.append({
            'timestamp': timestamp,
            'content': current_section
        })
    
    # 找到最新的本程序生成内容
    new_content_timestamp = extract_timestamp(steam_hosts_content)
    latest_program_section = None
    latest_timestamp = datetime.min
    
    for section in sections:
        if section['timestamp'] != datetime.max:  # 排除系统原有内容
            if section['timestamp'] > latest_timestamp:
                latest_timestamp = section['timestamp']
                latest_program_section = section
    
    # 过滤内容：保留系统原有内容 + 丢弃旧的本程序内容 + 添加最新内容
    filtered_lines = []
    for section in sections:
        if section['timestamp'] == datetime.max:
            # 系统原有内容，保留
            filtered_lines.extend(section['content'])
        elif latest_program_section and section == latest_program_section:
            # 最新的本程序内容，保留
            filtered_lines.extend(section['content'])
        else:
            # 旧的本程序内容，丢弃
            logger.info("删除旧版本hosts生成内容: {}".format(section['timestamp']))
    
    # 添加新内容
    new_content = '\n'.join(filtered_lines).strip() + '\n\n' + steam_hosts_content + '\n'
    
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


def get_default_config():
    """获取默认配置"""
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


def init_config():
    """生成默认配置文件"""
    config_path = Path.cwd() / 'config.yaml'
    if config_path.exists():
        logger.warning("配置文件已存在: {}".format(config_path))
        return False

    config = get_default_config()
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    logger.info("已生成配置文件: {}".format(config_path))
    return True


def load_config():
    """加载配置文件"""
    config_path = get_config_path()
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f), config_path
    else:
        return get_default_config(), None


def update(install=True, output_file=None):
    """执行更新流程

    Args:
        install: 是否安装到系统hosts文件，默认True
        output_file: 输出文件路径，如果指定则只生成不安装
    """
    logger.info("=" * 50)
    logger.info("Steam Hosts更新程序启动")
    logger.info("=" * 50)

    # 如果指定了output_file，则不安装
    if output_file:
        install = False
        logger.info("输出模式: 仅生成hosts文件")

    # 加载配置
    config, config_path = load_config()
    if config_path:
        logger.info("加载配置文件: {}".format(config_path))
    else:
        logger.info("未找到配置文件，使用默认配置")

    domains = config.get('steam_domains', [])

    # 查询DNS
    entries = query_all_domains(domains)
    if not entries:
        raise DnsQueryError("没有成功查询到任何域名IP地址")

    # 写入hosts文件
    if output_file:
        hosts_file = output_file
    else:
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

    # 解析命令行参数
    output_only = '--output' in sys.argv or '-o' in sys.argv
    init_config_requested = '--init-config' in sys.argv
    show_help = '--help' in sys.argv or '-h' in sys.argv
    log_to_file = '--log' in sys.argv or '-l' in sys.argv

    # 获取输出文件路径
    output_file = None
    if output_only:
        try:
            # 优先检查--output
            if '--output' in sys.argv:
                output_index = sys.argv.index('--output')
                if output_index + 1 < len(sys.argv):
                    output_file = sys.argv[output_index + 1]
            # 如果没找到--output，检查-o
            elif '-o' in sys.argv:
                output_index = sys.argv.index('-o')
                if output_index + 1 < len(sys.argv):
                    output_file = sys.argv[output_index + 1]
        except ValueError:
            pass

    # 重新设置日志系统（如果需要输出到文件）
    if log_to_file:
        # 清除已存在的handlers，防止重复输出
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        setup_logging(log_to_file=True)

    try:
        if show_help:
            print("\n使用方法:")
            print("  SteamHosts_Updater.exe                    # 直接安装到系统（默认）")
            print("  SteamHosts_Updater.exe -o [filename]       # 只生成hosts文件，不安装")
            print("  SteamHosts_Updater.exe --output hosts.txt  # 只生成hosts文件，不安装")
            print("  SteamHosts_Updater.exe --log               # 生成日志文件")
            print("  SteamHosts_Updater.exe --init-config       # 生成默认配置文件")
            print("  SteamHosts_Updater.exe --help              # 显示帮助信息")
            print("")
            print("说明:")
            print("  - 默认行为：查询DNS并直接安装到系统hosts文件")
            print("  - --output/-o：只生成hosts文件到当前目录")
            print("  - --log/-l：同时将日志输出到文件（文件名精确到秒）")
            print("  - --init-config：生成config.yaml配置文件供高级用户自定义")
            print("  - 配置文件：如存在同级目录的config.yaml则加载，否则使用内置默认配置")
            return 0

        if init_config_requested:
            return 0 if init_config() else 1

        if output_only:
            # 只输出模式
            update(install=False, output_file=output_file)
        else:
            # 默认安装模式
            update(install=True)

    except Exception as e:
        print("\n[错误] {}".format(e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
