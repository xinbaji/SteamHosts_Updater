# Steam Hosts Updater

自动更新Steam相关域名的hosts文件，加速Steam访问。

## 功能特性

- ✅ 通过DNS查询Steam域名IP
- ✅ 自动生成hosts文件
- ✅ 支持Windows、macOS、Linux三平台
- ✅ 单文件可执行程序，无需安装依赖
- ✅ 一键安装到系统hosts
- ✅ 内置默认配置，开箱即用
- ✅ 支持自定义配置（可选）
- ✅ 支持日志文件输出（文件名精确到秒）

## 快速开始

### 使用可执行文件（推荐）

下载最新Release中的可执行文件并直接运行（当前版本：0.9.0）：

```bash
# Windows
SteamHosts_Updater_standalone_windows_X.X.X.exe          # 直接安装到系统（默认）
SteamHosts_Updater_standalone_windows_X.X.X.exe -o        # 只生成hosts文件到当前目录
SteamHosts_Updater_standalone_windows_X.X.X.exe --log      # 安装并生成日志文件

# macOS/Linux
./SteamHosts_Updater_standalone_ubuntu_X.X.X             # 直接安装到系统
./SteamHosts_Updater_standalone_ubuntu_X.X.X -o          # 只生成hosts文件到当前目录
./SteamHosts_Updater_standalone_ubuntu_X.X.X --log       # 安装并生成日志文件
```

**注意**：直接安装需要管理员/root权限

### 使用Python脚本

```bash
# 安装依赖
pip install -r requirements.txt

# 主程序（推荐）
python SteamHosts_Updater.py      # 直接安装到系统
python SteamHosts_Updater.py -o   # 只生成hosts文件
python SteamHosts_Updater.py --log # 安装并生成日志文件

# 独立查询模块（用于CI/CD或调试）
python query_dns.py              # 只生成hosts文件
python query_dns.py --log        # 生成hosts文件并保存日志

# 远程安装模块（功能已搁置）
# python install_hosts.py [URL]     # 从远程仓库下载并安装
# python install_hosts.py --log     # 安装并保存日志
```

## 命令行参数

### SteamHosts_Updater.py（主程序）

```bash
SteamHosts_Updater                    # 直接安装到系统（默认）
SteamHosts_Updater -o [filename]       # 只生成hosts文件，不安装
SteamHosts_Updater --output hosts.txt  # 指定输出文件名
SteamHosts_Updater --log              # 同时生成日志文件
SteamHosts_Updater -l                 # 同时生成日志文件（简写）
SteamHosts_Updater --init-config      # 生成默认配置文件
SteamHosts_Updater --help             # 显示帮助信息
```

### query_dns.py（独立查询模块）

```bash
python query_dns.py                    # 生成hosts文件
python query_dns.py --log              # 生成hosts文件并保存日志
python query_dns.py -l                 # 生成hosts文件并保存日志（简写）
```

### install_hosts.py（远程安装模块 - 功能已搁置）

> 注意：此模块功能暂时搁置，等待远程仓库接口建立。

```bash
python install_hosts.py --help         # 查看说明
```

## 配置说明

### 日志文件

默认情况下，日志只输出到控制台。使用 `--log` 或 `-l` 参数时，会同时生成日志文件：

**日志文件命名规则：**
- 主程序: `steam_hosts_updater_YYYYMMDD_HHMMSS.log`

文件名精确到秒，确保多次运行不会覆盖之前的日志。

### 默认配置

程序内置了默认配置，开箱即用，无需配置文件。

### 自定义配置（可选）

如需自定义配置，运行以下命令生成配置文件：

```bash
SteamHosts_Updater --init-config
```

生成的 `config.yaml` 支持以下配置：

```yaml
steam_domains:
  - store.steampowered.com
  - steamcommunity.com
  # ... 更多域名

dns:
  server: 8.8.8.8       # DNS服务器
  timeout: 5             # 超时时间（秒）

output:
  hosts_file: hosts      # 输出文件名

logging:
  level: INFO            # 日志级别
```

**注意**：配置文件需要放在可执行文件同级目录。

## 当前Hosts内容

**最后更新时间:** 2026-03-19 12:25:08

```hosts
184.31.113.220	store.steampowered.com
23.60.136.72	steamcommunity.com
23.60.136.72	api.steampowered.com
104.88.206.78	steamuserimages-a.akamaihd.net
23.54.76.12	steamcdn-a.akamaihd.net
104.88.206.72	steamcommunity-a.akamaihd.net
104.88.206.76	steamstore-a.akamaihd.net
23.38.125.16	steambroadcast.akamaized.net
184.25.123.171	steamvideo-a.akamaihd.net
23.60.136.72	help.steampowered.com
172.234.232.226	support.steampowered.com
23.2.95.19	steamgames.com
```

*完整内容请查看 [hosts](hosts) 文件*

## 工作流程

- **CI测试**: 每次push或PR时运行测试
- **每日更新**: 每天早8点自动查询更新
- **自动发版**: commit消息包含V开头时自动打包发布

## 项目结构

```
.
├── SteamHosts_Updater.py    # 主程序（单文件可执行版本）
├── query_dns.py             # 独立查询模块（生成hosts文件，不安装）
├── install_hosts.py         # 远程安装模块（功能已搁置）
├── config.yaml              # 配置文件（可选，使用 --init-config 生成）
├── hosts                   # 当前hosts文件
├── requirements.txt         # Python依赖
├── test_all.py             # 综合测试脚本
├── .github/
│   └── workflows/
│       ├── ci.yml           # CI工作流
│       ├── release.yml      # 发版工作流
│       └── daily_update.yml # 每日更新工作流
└── README.md
```

## 模块说明

| 模块 | 用途 | 特点 |
|------|------|------|
| `SteamHosts_Updater.py` | 主程序，推荐使用 | 直接安装到系统，支持配置，打包为单文件可执行程序 |
| `query_dns.py` | 独立查询模块 | 只生成hosts文件，不安装，适合CI/CD和调试 |
| `install_hosts.py` | 远程安装模块 | 功能暂时搁置，等待远程仓库接口建立 |

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

