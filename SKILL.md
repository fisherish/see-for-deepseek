---
name: doubao-vision
description: Recognize and describe image content using Doubao vision API. Pass an image path (local or URL) and get back a detailed text description of the image contents.
argument-hint: <image-path-or-url | --from-session>
---

# Doubao Vision

Use Doubao (ByteDance) vision model to analyze and describe an image. This skill gives text-only LLMs (like DeepSeek) in Claude Code the ability to "see" images.

## When to use

- Main model encounters an image and needs to know its contents
- Need to extract text, objects, scenes, or layout information from an image
- Image is in a local file, accessible via URL, or pasted in the conversation

## How to use effectively

### 1. Craft context-specific prompts

**Do NOT** use the generic default prompt. Always customize `--prompt` based on what you need from the image in the current task:

```bash
# Instead of: python vision.py img.png  (uses generic "describe everything" prompt)
# Do:
python ~/.claude/skills/doubao-vision/scripts/vision.py img.png --prompt "截图中有哪些错误信息？请详细列出所有文字内容"
python ~/.claude/skills/doubao-vision/scripts/vision.py img.png --prompt "Describe the chart: axes labels, data trends, and legend"
python ~/.claude/skills/doubao-vision/scripts/vision.py img.png --prompt "这张图片里有哪些物体？它们的空间位置关系如何？"
```

### 2. Iterate with follow-up questions

If the first result isn't sufficient, use `-q` to ask follow-up questions about the same image (reuses cached image, no need to re-send):

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session -q "左上角那个按钮上的图标是什么意思？"
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session -q "What font size is the title?"
```

Keep iterating with follow-ups until the visual information needed for the task is fully gathered.

## Quick reference

### Local file or URL

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py <path-or-url> --prompt "<your-specific-question>"
```

### Image pasted in conversation

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session --prompt "<your-specific-question>"
```

### Follow-up question

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session -q "<follow-up-question>"
```

## Available models

- `doubao-seed-1-6-flash-250615` (default) — fast, supports image/video input
- `doubao-seed-2-0-lite-260428` — full-modal, higher quality

Auto-fallback: if default model is unavailable, tries the other.

## Requirements

- `DOUBAO_API_KEY` environment variable must be set (Volcengine Ark API key)
- Python package `requests` must be installed
