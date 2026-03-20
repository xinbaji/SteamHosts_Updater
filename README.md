# Steam Hosts Updater

自动更新Steam相关域名的hosts文件，加速Steam访问。

## 功能特性

- ✅ 通过Google DNS (8.8.8.8) 查询Steam域名IP
- ✅ 自动生成hosts文件
- ✅ 支持Windows、macOS、Linux三平台
- ✅ 单文件可执行程序，无需安装依赖
- ✅ 每日自动更新
- ✅ 支持一键安装到系统hosts
- ✅ 完善的错误处理和日志记录

## 快速开始

### 方法1: 使用可执行文件（推荐）

下载最新Release中的可执行文件：
- Windows: `steam_hosts_updater_windows.exe`
- macOS: `steam_hosts_updater_macos`
- Linux: `steam_hosts_updater_ubuntu`

**步骤：**

1. 仅生成hosts文件：
   ```bash
   # Windows
   steam_hosts_updater_windows.exe

   # macOS/Linux
   ./steam_hosts_updater_macos
   # 或
   ./steam_hosts_updater_ubuntu
   ```

2. 生成并安装到系统hosts（需要管理员/root权限）：
   ```bash
   # Windows（右键"以管理员身份运行"）
   steam_hosts_updater_windows.exe --install
   # 或
   steam_hosts_updater_windows.exe -i

   # macOS/Linux
   sudo ./steam_hosts_updater_macos --install
   # 或
   sudo ./steam_hosts_updater_ubuntu --install
   ```

### 方法2: 使用Python脚本

```bash
# 安装依赖
pip install -r requirements.txt

# 仅生成hosts文件
python SteamHosts_Updater.py

# 生成并安装到系统hosts（需要管理员/root权限）
python SteamHosts_Updater.py --install
# 或
python SteamHosts_Updater.py -i
```

## 配置说明

编辑 `config.yaml` 文件可以自定义：
- Steam域名列表
- DNS服务器地址
- 超时时间
- 日志级别

## 当前Hosts内容

**最后更新时间:** 2026-03-20 01:46:27

```hosts
23.62.177.63	store.steampowered.com
23.222.161.105	steamcommunity.com
23.222.161.105	api.steampowered.com
23.56.109.231	steamuserimages-a.akamaihd.net
23.56.109.199	steamcdn-a.akamaihd.net
23.56.109.236	steamcommunity-a.akamaihd.net
23.56.109.229	steamstore-a.akamaihd.net
23.217.118.139	steambroadcast.akamaized.net
23.217.118.200	steamvideo-a.akamaihd.net
23.222.161.105	help.steampowered.com
172.234.232.226	support.steampowered.com
23.40.174.97	steamgames.com
23.56.109.236	store.akamai.steamstatic.com
23.56.109.231	cdn.akamai.steamstatic.com
23.40.174.97	steam-chat.com
23.56.109.234	community.akamai.steamstatic.com
```

*完整内容请查看 [hosts](hosts) 文件*

## 工作流程

- **CI测试**: 每次push或PR时运行测试
- **每日更新**: 每天早8点自动查询更新
- **自动发版**: commit消息包含V开头时自动打包发布

## 项目结构

```
.
├── config.yaml              # 配置文件
├── SteamHosts_Updater.py    # 单文件完整功能脚本（推荐）
├── query_dns.py             # DNS查询脚本（独立）
├── install_hosts.py         # 安装脚本（独立）
├── test_query_dns.py        # 测试脚本
├── requirements.txt         # Python依赖
├── .github/
│   └── workflows/
│       ├── ci.yml           # CI工作流
│       ├── release.yml      # 发版工作流
│       └── daily_update.yml # 每日更新工作流
└── README.md
```

## 故障排除

### 权限错误
- **Windows**: 右键"以管理员身份运行"
- **macOS/Linux**: 使用 `sudo` 运行

### DNS查询失败
- 检查网络连接
- 尝试更换DNS服务器
- 增加timeout配置值

### 安装失败
- 确认有写入hosts文件的权限
- 检查文件是否被其他程序占用
- 查看详细错误日志

## 许可证

MIT License

