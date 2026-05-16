---
name: doubao-vision
description: Recognize and describe image content using Doubao vision API. Pass an image path (local or URL) and get back a detailed text description of the image contents.
argument-hint: <image-path-or-url | --from-session>
---

# Doubao Vision

Use Doubao (ByteDance) vision model to analyze and describe an image.

## When to use

- Main model encounters an image and needs to know its contents
- Need to extract text, objects, scenes, or layout information from an image
- Image is in a local file, accessible via URL, or pasted in the conversation

## Usage

### Local file or URL

Pass the file path or URL directly:

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py <path-or-url>
```

### Image pasted in conversation (first description)

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session
```

### Follow-up questions about the same image

After the initial description, ask specific details without re-sending the image:

```bash
python ~/.claude/skills/doubao-vision/scripts/vision.py --from-session -q "What text is in the top-left corner?"
```

The `-q` / `--question` parameter reuses the cached image from the previous description.

## Available models

- `doubao-seed-1-6-flash-250615` (default) — fast, supports image/video input
- `doubao-seed-2-0-lite-260428` — full-modal, higher quality

Auto-fallback: if default model is unavailable, tries the other.

## Requirements

- `DOUBAO_API_KEY` environment variable must be set (Volcengine Ark API key)
- Python package `requests` must be installed
