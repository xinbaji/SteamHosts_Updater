#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Steam Hosts安装脚本

该脚本从远程仓库获取hosts文件，备份本地hosts文件，
然后将Steam hosts内容追加到本地hosts文件末尾。
支持Windows、macOS和Linux三平台。
"""

import logging
import os
import platform
import subprocess
import shutil
from pathlib import Path
import requests


class HostsInstallError(Exception):
    """Hosts安装异常类"""
    pass


class HostsInstaller:
    """Hosts文件安装器"""
    
    # 各平台的hosts文件路径
    HOSTS_PATHS = {
        'Windows': r'C:\\Windows\\System32\\drivers\\etc\\hosts',
        'Darwin': '/etc/hosts',
        'Linux': '/etc/hosts'
    }
    
    # DNS刷新命令
    DNS_FLUSH_COMMANDS = {
        'Windows': ['ipconfig', '/flushdns'],
        'Darwin': ['sudo', 'dscacheutil', '-flushcache'],
        'Linux': ['sudo', 'systemctl', 'restart', 'nscd']
    }
    
    def __init__(
        self,
        repo_url: str | None = None,
        hosts_file_path: str | None = None
    ) -> None:
        """初始化安装器
        
        Args:
            repo_url: 远程仓库的raw文件URL
            hosts_file_path: 本地hosts文件路径（可选，默认自动检测）
        """
        self.system = platform.system()
        self.logger = self._setup_logging()
        self.remote_url = repo_url or self._get_default_repo_url()
        
        # 获取hosts文件路径
        self.hosts_path: str
        if hosts_file_path:
            self.hosts_path = hosts_file_path
        else:
            self.hosts_path = self.HOSTS_PATHS.get(self.system, '')
        
        # 验证系统支持
        if not self.hosts_path:
            raise HostsInstallError(
                f"不支持的操作系统: {self.system}\n"
                f"支持的系统: Windows, macOS (Darwin), Linux"
            )
        
        self.logger.info(f"系统: {self.system}")
        self.logger.info(f"Hosts文件路径: {self.hosts_path}")
    
    def _setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _get_default_repo_url(self) -> str:
        """获取默认的仓库URL
        
        Returns:
            默认的hosts文件raw URL
        """
        # 用户应配置为自己的仓库URL
        return "https://raw.githubusercontent.com/yourusername/steam_hosts_updater/main/hosts"
    
    def _check_admin_privileges(self) -> bool:
        """检查是否有管理员权限
        
        Returns:
            是否有管理员权限
        """
        if self.system == 'Windows':
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception:
                return False
        else:
            # Unix-like系统检查
            return os.access('/etc', os.W_OK)
    
    def download_remote_hosts(self) -> str:
        """从远程仓库下载hosts文件
        
        Returns:
            下载的hosts文件内容
            
        Raises:
            HostsInstallError: 下载失败
        """
        self.logger.info(f"从远程下载hosts文件: {self.remote_url}")
        
        try:
            response = requests.get(self.remote_url, timeout=10)
            response.raise_for_status()
            
            content = response.text
            self.logger.info(f"成功下载hosts文件，大小: {len(content)} 字节")
            return content
            
        except requests.exceptions.Timeout:
            raise HostsInstallError(
                "下载超时，请检查网络连接。\n"
                "可能的解决方案:\n"
                "1. 检查网络连接\n"
                "2. 尝试更换网络环境\n"
                "3. 检查仓库URL是否正确"
            )
        except requests.exceptions.HTTPError as e:
            raise HostsInstallError(
                f"HTTP错误: {e}\n"
                "可能的解决方案:\n"
                "1. 检查仓库URL是否正确\n"
                "2. 确认仓库中是否存在hosts文件\n"
                "3. 检查仓库是否为公开仓库"
            )
        except Exception as e:
            raise HostsInstallError(
                f"下载失败: {e}\n"
                "请联系技术支持"
            )
    
    def backup_hosts_file(self) -> str:
        """备份本地hosts文件
        
        Returns:
            备份文件路径
        """
        hosts_file = Path(self.hosts_path)
        backup_dir = Path.home() / '.steam_hosts_updater' / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成备份文件名
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'hosts_{timestamp}.backup'
        
        try:
            if hosts_file.exists():
                shutil.copy2(self.hosts_path, backup_file)
                self.logger.info(f"已备份hosts文件到: {backup_file}")
            else:
                self.logger.warning(f"原hosts文件不存在，跳过备份")
                backup_file.touch()  # 创建空备份文件
        except Exception as e:
            raise HostsInstallError(
                f"备份失败: {e}\n"
                "可能的解决方案:\n"
                "1. 检查是否有读取权限\n"
                "2. 检查磁盘空间是否充足\n"
                "3. 检查文件是否被其他程序占用"
            )
        
        return str(backup_file)
    
    def parse_steam_hosts(self, content: str) -> str:
        """解析Steam hosts内容
        
        Args:
            content: 远程hosts文件内容
            
        Returns:
            Steam hosts内容（不包含外层注释）
        """
        lines = content.split('\n')
        steam_hosts = []
        in_steam_section = False
        
        for line in lines:
            # 检测开始标记
            if 'Steam Hosts - 由程序自动生成' in line:
                in_steam_section = True
            # 检测结束标记
            elif 'Steam Hosts结束' in line:
                in_steam_section = False
            # 收集内容
            elif in_steam_section:
                steam_hosts.append(line)
        
        return '\n'.join(steam_hosts).strip()
    
    def update_hosts_file(self, steam_hosts_content: str) -> None:
        """更新本地hosts文件
        
        Args:
            steam_hosts_content: Steam hosts内容
        """
        hosts_file = Path(self.hosts_path)
        
        try:
            # 读取现有hosts内容
            existing_content = ""
            if hosts_file.exists():
                with open(hosts_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # 移除旧的Steam hosts
            lines = existing_content.split('\n')
            filtered_lines = []
            in_steam_section = False
            
            for line in lines:
                if 'Steam Hosts - 由程序自动生成' in line:
                    in_steam_section = True
                elif 'Steam Hosts结束' in line:
                    in_steam_section = False
                elif not in_steam_section:
                    filtered_lines.append(line)
            
            # 构建新内容
            new_content = '\n'.join(filtered_lines).strip() + '\n\n'
            new_content += steam_hosts_content + '\n'
            
            # 写入新内容
            with open(hosts_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.logger.info(f"成功更新hosts文件: {self.hosts_path}")
            
        except PermissionError:
            raise HostsInstallError(
                "权限不足，无法写入hosts文件。\n"
                "可能的解决方案:\n"
                "Windows:\n"
                "  以管理员身份运行此程序（右键 -> 以管理员身份运行）\n"
                "macOS/Linux:\n"
                "  使用sudo运行此程序：sudo python3 install_hosts.py"
            )
        except IOError as e:
            raise HostsInstallError(
                f"写入hosts文件失败: {e}\n"
                "可能的解决方案:\n"
                "1. 检查是否有写入权限\n"
                "2. 确认磁盘空间充足\n"
                "3. 检查文件是否被其他程序占用"
            )
        except Exception as e:
            raise HostsInstallError(
                f"更新hosts文件失败: {e}\n"
                "请联系技术支持"
            )
    
    def flush_dns_cache(self) -> None:
        """刷新DNS缓存"""
        command = self.DNS_FLUSH_COMMANDS.get(self.system)
        
        if not command:
            self.logger.warning(f"当前系统不支持自动刷新DNS: {self.system}")
            return
        
        try:
            self.logger.info(f"刷新DNS缓存: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("DNS缓存刷新成功")
            else:
                self.logger.warning(f"DNS刷新命令执行失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.logger.warning("DNS刷新命令执行超时")
        except FileNotFoundError:
            self.logger.warning("DNS刷新命令未找到，可能需要手动刷新")
        except Exception as e:
            self.logger.warning(f"DNS刷新失败: {e}")
    
    def install(self, repo_url: str | None = None) -> None:
        """执行安装流程
        
        Args:
            repo_url: 远程仓库URL（可选）
        """
        if repo_url:
            self.remote_url = repo_url
        
        try:
            self.logger.info("=" * 50)
            self.logger.info("Steam Hosts安装程序启动")
            self.logger.info("=" * 50)
            
            # 检查权限
            if not self._check_admin_privileges():
                raise HostsInstallError(
                    "需要管理员/root权限才能修改hosts文件。\n"
                    f"\n系统: {self.system}\n"
                    "\n解决方案:\n"
                    "Windows: 以管理员身份运行此程序\n"
                    "macOS/Linux: 使用sudo运行此程序"
                )
            
            # 下载远程hosts
            remote_content = self.download_remote_hosts()
            
            # 备份本地hosts
            self.backup_hosts_file()
            
            # 解析Steam hosts
            steam_hosts = self.parse_steam_hosts(remote_content)
            
            if not steam_hosts:
                raise HostsInstallError(
                    "未在远程hosts文件中找到Steam hosts内容。\n"
                    "请确认远程仓库的hosts文件格式正确。"
                )
            
            # 更新本地hosts
            self.update_hosts_file(steam_hosts)
            
            # 刷新DNS
            self.flush_dns_cache()
            
            self.logger.info("=" * 50)
            self.logger.info("Steam Hosts安装完成")
            self.logger.info("=" * 50)
            
        except HostsInstallError as e:
            self.logger.error(f"安装失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"未知错误: {e}")
            raise HostsInstallError(f"安装失败: {e}")


def main():
    """主函数"""
    import sys
    
    # 支持命令行参数指定仓库URL
    repo_url = None
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    
    try:
        installer = HostsInstaller(repo_url=repo_url)
        installer.install()
    except HostsInstallError as e:
        print(f"\n❌ 错误: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
