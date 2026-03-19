# Steam Hosts Updater

自动更新Steam相关域名的hosts文件，加速Steam访问。

## 功能特性

- ✅ 通过Google DNS (8.8.8.8) 查询Steam域名IP
- ✅ 自动生成hosts文件
- ✅ 支持Windows、macOS、Linux三平台
- ✅ 每日自动更新
- ✅ 支持一键安装到系统hosts
- ✅ 完善的错误处理和日志记录

## 快速开始

### 方法1: 使用可执行文件（推荐）

下载最新Release中的可执行文件：
- Windows: `query_dns_windows.exe`, `install_hosts_windows.exe`
- macOS: `query_dns_macos`, `install_hosts_macos`
- Linux: `query_dns_ubuntu`, `install_hosts_ubuntu`

**步骤：**
1. 运行查询脚本生成hosts文件
2. 以管理员权限运行安装脚本

### 方法2: 使用Python脚本

```bash
# 安装依赖
pip install -r requirements.txt

# 查询并生成hosts文件
python query_dns.py

# 安装到系统hosts（需要管理员/root权限）
python install_hosts.py
```

## 配置说明

编辑 `config.yaml` 文件可以自定义：
- Steam域名列表
- DNS服务器地址
- 超时时间
- 日志级别

## 当前Hosts内容

**最后更新时间:** 2026-03-19

完整内容请查看 [hosts](hosts) 文件

## 工作流程

- **CI测试**: 每次push或PR时运行测试
- **每日更新**: 每天早8点自动查询更新
- **自动发版**: commit消息包含V开头时自动打包发布

## 项目结构

```
.
├── config.yaml              # 配置文件
├── query_dns.py             # DNS查询脚本
├── install_hosts.py         # 安装脚本
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
