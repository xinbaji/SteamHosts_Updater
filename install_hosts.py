#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Steam Hosts安装脚本（功能已搁置）

该脚本从远程仓库获取hosts文件，备份本地hosts文件，
然后将Steam hosts内容追加到本地hosts文件末尾。
支持Windows、macOS和Linux三平台。

注意：此脚本功能暂时搁置，等待远程仓库接口建立。

如需安装hosts文件，请使用 SteamHosts_Updater.py
"""


def main():
    """主函数"""
    print("=" * 70)
    print("install_hosts.py 功能暂时搁置")
    print("=" * 70)
    print("")
    print("原因：远程仓库接口尚未建立")
    print("")
    print("替代方案：")
    print("  1. 使用 SteamHosts_Updater.py 直接安装hosts到系统")
    print("  2. 使用 query_dns.py 生成hosts文件，然后手动安装")
    print("")
    print("如需帮助，请运行:")
    print("  python SteamHosts_Updater.py --help")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    exit(main())
