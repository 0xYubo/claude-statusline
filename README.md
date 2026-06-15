# Claude Statusline

🎨 Claude Code 状态监控面板 - 在终端底部实时显示 API 用量和 Context 使用率。

![Claude Statusline](https://img.shields.io/badge/claude--code-statusline-brightgreen?style=flat-square&logo=anthropic)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.8+-yellow?style=flat-square&logo=python)

## ✨ 功能特性

- 🎯 **实时监控** - 底部状态栏显示 Context、5h 用量、Weekly 用量
- 📊 **彩色进度条** - 根据使用量自动变色（绿→黄→红）
- ⏱️ **重置倒计时** - 精确显示额度重置剩余时间
- 🔄 **自动刷新** - 每 30 秒自动更新（可自定义）
- 💻 **多终端共享** - 多个窗口读取同一份数据
- 🚀 **零依赖** - 仅需 Python 3.8+

## 📸 预览效果

```
[mimo-v2.5] │ Context ████████░░ 45% │ Usage ██████████ 100% (resets in 24m) │ Weekly ███░░░░░░░ 38% (resets in 79h 14m)
```

颜色说明：
- 🟢 绿色: `< 70%` - 安全
- 🟡 黄色: `70-90%` - 警告
- 🔴 红色: `> 90%` - 即将耗尽

## 🚀 快速开始

### 方式一：直接安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/claude-statusline.git
cd claude-statusline

# 运行安装脚本
chmod +x install.sh
./install.sh
```

安装内容：
- 脚本复制到 `~/Developer/claude-statusline/`
- 创建符号链接到 `~/.local/bin/claude-statusline`

### 方式二：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/claude-statusline.git
cd claude-statusline

# 2. 创建目录
mkdir -p ~/Developer/claude-statusline

# 3. 复制文件
cp statusline.py ~/Developer/claude-statusline/
chmod +x ~/Developer/claude-statusline/statusline.py

# 4. 配置 Claude Code
```

编辑 `~/.claude/settings.json`，添加：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/Developer/claude-statusline/statusline.py",
    "refreshInterval": 30
  }
}
```

### 方式三：使用 Homebrew（如果有）

```bash
# 等待社区维护...
```

## ⚙️ 配置说明

### Claude Code 配置

编辑 `~/.claude/settings.json`：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /path/to/statusline.py",
    "refreshInterval": 30,  // 刷新间隔（秒）
    "hideVimModeIndicator": false  // 是否隐藏 vim 模式指示器
  }
}
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CLAUDE_CONFIG_DIR` | `~/.claude` | Claude 配置目录 |

## 📁 文件结构

```
claude-statusline/
├── statusline.py      # 主程序
├── install.sh         # 安装脚本
├── README.md          # 文档
├── LICENSE            # MIT 许可证
└── .gitignore
```

## 🔧 独立使用（TUI 模式）

除了集成到 Claude Code，还可以作为独立的终端监控面板：

```bash
# 默认 30s 刷新
python3 statusline.py

# 10s 刷新
python3 statusline.py -i 10

# 只显示一次
python3 statusline.py --once
```

## 🐛 故障排除

### 数据显示 0% 或 N/A

Claude Code 需要至少一次 API 调用后才会写入用量数据。使用 Claude Code 发送一条消息后再试。

### 进度条不显示颜色

确保你的终端支持 ANSI 颜色。大多数现代终端都支持。

### 权限错误

```bash
chmod +x ~/Developer/claude-statusline/statusline.py
```

### 配置不生效

1. 确认 `~/.claude/settings.json` 语法正确（可用 `jq .` 检查）
2. 重启 Claude Code
3. 检查 Python 路径是否正确

## 📊 数据来源

| 数据 | 来源文件 |
|------|----------|
| 5h/7d 用量 | `~/.claude/vscode-claude-status-cache.json` |
| Context | Claude Code 运行时传入 |
| 模型信息 | `~/.claude/settings.json` |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Claude Code](https://github.com/anthropics/claude-code) - Anthropic 官方 CLI
- [Rich](https://github.com/Textualize/rich) - Python 终端美化库（TUI 模式使用）

## 📮 联系方式

- Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/claude-statusline/issues)
- Email: your.email@example.com

---

⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！
