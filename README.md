# Doubao Vision — Claude Code Vision Skill

豆包看图 —— 为 Claude Code 赋予图像识别能力

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)

---

> **English** | [中文](#简介)

## Introduction

**Doubao Vision** is a [Claude Code](https://claude.ai/code) skill that enables Claude to analyze and describe images by calling ByteDance's Doubao vision models through the [Volcengine Ark](https://console.volcengine.com/ark) platform.

Claude Code itself is text-only and cannot see images. This skill bridges that gap: when Claude encounters an image (local file, URL, or pasted in conversation), it delegates visual understanding to Doubao's powerful vision models and receives a detailed text description.

### Features

- **Local images** — Pass any local image file path
- **URL images** — Pass an image URL
- **Session images** — Auto-extract images pasted in Claude Code conversation (`--from-session`)
- **Follow-up questions** — Ask specific questions about a cached image without re-sending (`-q`)
- **Auto-compression** — Compresses large images to stay within API limits (via PIL)
- **Auto-fallback** — Falls back to secondary model if the primary is unavailable
- **Retry logic** — Connection pooling & exponential backoff for network resilience
- **Multi-format** — Supports JPEG, PNG, GIF, WebP, BMP

### Supported Models

| Model | Description |
|-------|-------------|
| `doubao-seed-1-6-flash-250615` | Default — fast, supports image/video input |
| `doubao-seed-2-0-lite-260428` | Full-modal fallback — higher quality |

---

## 简介

**豆包看图** 是一个 [Claude Code](https://claude.ai/code) 技能，通过调用火山引擎方舟平台上的豆包视觉模型，让 Claude Code 能够"看懂"图片内容。

Claude Code 本身是纯文本模型，无法直接处理图片。这个技能弥补了这一限制：当 Claude 遇到图片（本地文件、URL 或对话中粘贴的图片）时，它会调用豆包视觉模型进行分析，并获取详细的文字描述。

### 功能特点

- **本地图片** — 传入任意本地图片路径
- **网络图片** — 传入图片 URL
- **会话图片** — 自动提取 Claude Code 对话中粘贴的图片（`--from-session`）
- **追问图片** — 基于缓存的图片追问细节，无需重复发送（`-q`）
- **自动压缩** — 自动压缩大图以满足 API 限制（需 PIL）
- **自动降级** — 主模型不可用时自动切换备用模型
- **重试机制** — 连接池与指数退避重试
- **多格式支持** — JPEG、PNG、GIF、WebP、BMP

### 支持模型

| 模型 | 说明 |
|------|------|
| `doubao-seed-1-6-flash-250615` | 默认 — 快速响应，支持图像/视频输入 |
| `doubao-seed-2-0-lite-260428` | 备用 — 全模态，质量更高 |

---

## Prerequisites / 前置要求

- [Claude Code](https://claude.ai/code) installed
- Python 3.9+
- A [Volcengine Ark](https://console.volcengine.com/ark) account with Doubao vision model access
- API key from Volcengine Ark console

## Installation / 安装

### 1. Install Python dependencies

```bash
pip install requests Pillow
```

> `Pillow` is optional but recommended — without it, large images won't be auto-compressed.

### 2. Copy the skill files

```bash
# Clone the repo
git clone https://github.com/<your-username>/doubao-vision.git

# Copy to Claude Code skills directory
cp -r doubao-vision ~/.claude/skills/doubao-vision
```

Or create a symlink (recommended for easy updates):

```bash
ln -s $(pwd)/doubao-vision ~/.claude/skills/doubao-vision
```

### 3. Set the API key

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export DOUBAO_API_KEY="your-api-key-here"
```

Get your API key from the [Volcengine Ark console](https://console.volcengine.com/ark).

> On Windows: set via System Environment Variables or add to your PowerShell profile.

### 4. Verify installation

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py /path/to/test-image.png
```

You should see a detailed description of the image.

---

## Usage / 使用方法

### Local file / 本地图片

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py /path/to/image.jpg
```

### URL / 网络图片

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py https://example.com/image.jpg
```

### Pasted image (Claude Code conversation) / 对话中粘贴的图片

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session
```

### Follow-up question / 追问图片

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session -q "图片左上角的文字是什么？"
```

### Custom prompt / 自定义提示词

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py image.png --prompt "Describe only the colors and lighting"
```

### Specify model / 指定模型

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py image.png --model doubao-seed-2-0-lite-260428
```

---

## Claude Code Skill Configuration

This project is designed as a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills). Once installed in `~/.claude/skills/doubao-vision/`, Claude Code can invoke it automatically via the skill dispatch system.

The skill is registered with the ID `doubao-vision` and accepts an image path, URL, or `--from-session` as argument.

### Register the skill manually

If auto-detection doesn't work, add to `~/.claude/.claude.json`:

```json
{
  "skills": {
    "doubao-vision": {
      "usageCount": 0
    }
  }
}
```

---

## Project Structure / 项目结构

```
doubao-vision/
├── README.md                # This file
├── LICENSE                  # MIT License
├── requirements.txt         # Python dependencies
├── .gitignore
├── SKILL.md                 # Claude Code skill definition
└── scripts/
    └── vision.py            # Doubao vision API client
```

---

## How It Works / 工作原理

```
User/Claude Code
    │
    ▼
doubao-vision skill (SKILL.md)
    │
    ▼
vision.py
    │  ├─ Reads/ downloads image
    │  ├─ Encodes to base64
    │  └─ Calls Doubao API (OpenAI-compatible endpoint)
    │
    ▼
Doubao vision model (Volcengine Ark)
    │
    ▼
Text description → Claude Code
```

---

## Configuration / 配置

| Variable | Description |
|----------|-------------|
| `DOUBAO_API_KEY` | (Required) Volcengine Ark API key |
| `TEMP` | (Optional) Custom temp directory for cached session images |

---

## Acknowledgments / 致谢

- [ByteDance Doubao](https://www.volcengine.com/product/doubao) — vision model provider
- [Volcengine Ark](https://console.volcengine.com/ark) — API platform
- [Claude Code](https://claude.ai/code) — the AI assistant that uses this skill

---

## License / 许可

[MIT](LICENSE)
