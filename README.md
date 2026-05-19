# Steam Hosts Updater

自动更新Steam相关域名的hosts文件，加速Steam访问。

## 功能特性

- ✅ 通过DNS API查询Steam域名IP（快速稳定）
- ✅ 自动生成hosts文件
- ✅ 支持Windows、macOS、Linux三平台
- ✅ 单文件可执行程序，无需安装依赖
- ✅ 每日自动更新
- ✅ 支持一键安装到系统hosts
- ✅ 完善的错误处理和日志记录
- ✅ 支持自定义配置文件

## 快速开始

### 方法1: 使用可执行文件（推荐）

下载最新Release中的可执行文件：
- Windows: `SteamHosts_Updater_standalone_windows_V*.exe`
- macOS: `SteamHosts_Updater_standalone_macos_V*`
- Linux: `SteamHosts_Updater_standalone_ubuntu_V*`

**使用方法：**

```bash
# 1. 直接安装到系统hosts（默认行为，需要管理员权限）
# Windows（右键"以管理员身份运行"）
SteamHosts_Updater_standalone_windows.exe

# macOS/Linux
sudo ./SteamHosts_Updater_standalone_macos

# 2. 仅生成hosts文件（不安装）
SteamHosts_Updater_standalone_windows.exe -o hosts
# 或
SteamHosts_Updater_standalone_windows.exe --output hosts

# 3. 生成日志文件
SteamHosts_Updater_standalone_windows.exe --log

# 4. 生成配置文件模板
SteamHosts_Updater_standalone_windows.exe --init-config

# 5. 查看帮助
SteamHosts_Updater_standalone_windows.exe --help
```

### 方法2: 使用Python脚本

```bash
# 安装依赖
pip install -r requirements.txt

# 直接安装到系统hosts（默认行为，需要管理员权限）
# Windows（以管理员身份运行）
python SteamHosts_Updater.py

# macOS/Linux
sudo python SteamHosts_Updater.py

# 仅生成hosts文件（不安装）
python SteamHosts_Updater.py -o hosts

# 生成日志文件
python SteamHosts_Updater.py --log

# 生成配置文件模板
python SteamHosts_Updater.py --init-config

# 查看帮助
python SteamHosts_Updater.py --help
```

## 命令行参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| 无参数 | - | 默认直接安装到系统hosts文件（需要管理员权限） |
| `--output <file>` | `-o <file>` | 仅生成hosts文件到指定路径，不安装 |
| `--log` | `-l` | 生成日志文件（格式：steam_hosts_updater_YYYYMMDD_HHMMSS.log） |
| `--init-config` | - | 生成默认配置文件模板 config.yaml |
| `--help` | `-h` | 显示帮助信息 |

## 配置说明

程序支持自定义配置文件。运行 `--init-config` 生成 `config.yaml` 模板：

```yaml
# Steam域名列表
steam_domains:
  - store.steampowered.com
  - steamcommunity.com
  - api.steampowered.com
  # ... 更多域名

# DNS API配置
dns_api:
  url: "https://dns.google/resolve"
  timeout: 10

# 日志配置
logging:
  level: INFO
```

配置策略：
- 如果同级目录存在 `config.yaml`，则加载用户配置
- 否则使用内置默认配置

## 其他脚本说明

### query_dns.py

独立DNS查询脚本，用于CI工作流自动更新：

```bash
# 直接运行，生成hosts文件
python query_dns.py
```

**注意：** 此脚本不支持命令行参数，仅用于自动化工作流。

### install_hosts.py

远程安装模块（功能已搁置，等待远程仓库接口支持）。

## 当前Hosts内容

**最后更新时间:** 2026-05-19 02:46:38

```hosts
184.29.31.209	store.steampowered.com
23.64.158.119	steamcommunity.com
23.64.158.119	api.steampowered.com
23.219.89.206	steamuserimages-a.akamaihd.net
23.47.48.78	steamcdn-a.akamaihd.net
23.219.89.196	steamcommunity-a.akamaihd.net
23.219.89.206	steamstore-a.akamaihd.net
23.47.52.55	steambroadcast.akamaized.net
23.47.50.202	steamvideo-a.akamaihd.net
23.64.158.119	help.steampowered.com
172.234.232.226	support.steampowered.com
23.59.109.20	steamgames.com
23.219.89.206	store.akamai.steamstatic.com
23.219.89.219	cdn.akamai.steamstatic.com
23.59.109.20	steam-chat.com
23.219.89.196	community.akamai.steamstatic.com
```

*完整内容请查看 [hosts](hosts) 文件*

## 工作流程

- **CI测试**: 每次push或PR时运行测试
- **每日更新**: 每天早8点自动查询更新
- **自动发版**: commit消息包含V开头时自动打包发布

## 项目结构

```
.
├── config.yaml              # 配置文件（可选）
├── SteamHosts_Updater.py    # 主程序（支持所有参数）
├── query_dns.py             # DNS查询脚本（仅用于CI）
├── install_hosts.py         # 远程安装模块（搁置）
├── test_all.py              # 测试脚本
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
- 尝试更换DNS API地址
- 增加timeout配置值

### 安装失败
- 确认有写入hosts文件的权限
- 检查文件是否被其他程序占用
- 使用 `--log` 参数查看详细日志

## 许可证

MIT License

