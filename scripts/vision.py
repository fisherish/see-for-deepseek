#!/usr/bin/env python3
"""Call Doubao vision API to describe an image.

Supports:
  - Local image path
  - Image URL
  --from-session: auto-extract latest image from Claude Code session log
"""

import argparse
import base64
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-1-6-flash-250615"
FALLBACK_MODEL = "doubao-seed-2-0-lite-260428"
MAX_RETRIES = 2
TIMEOUT = 30  # shorter timeout, rely on retries
CACHE_PATH = Path(os.environ.get("TEMP", "/tmp")) / "doubao_session_image.png"


def create_session() -> requests.Session:
    """Create a session with connection pooling and retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        read=2,
        connect=2,
        backoff_factor=1,  # 1s, 2s, 4s
        allowed_methods=["POST"],
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        pool_connections=4,
        pool_maxsize=10,
        max_retries=retry,
    )
    session.mount("https://", adapter)

    # Disable cert verification warning noise
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return session


def compress_image(image_path: str, max_size: int = 500 * 1024) -> tuple[bytes, str]:
    """Compress image if it exceeds max_size. Returns (image_bytes, media_type)."""
    from PIL import Image as PILImage

    path = Path(image_path)
    suffix = path.suffix.lower()
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    }.get(suffix, "image/png")

    original_size = path.stat().st_size
    if original_size <= max_size:
        with open(path, "rb") as f:
            return f.read(), media_type

    img = PILImage.open(path)
    # Convert RGBA to RGB for JPEG compression
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Reduce quality iteratively until under max_size
    quality = 85
    while quality >= 20:
        buf = BytesIO()
        if media_type == "image/png":
            # PNG doesn't support quality; try reducing dimensions
            break
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= max_size:
            return buf.getvalue(), "image/jpeg"
        quality -= 10

    # If still too large, reduce dimensions
    scale = 1.0
    while True:
        w = int(img.width * scale)
        h = int(img.height * scale)
        if w < 100 or h < 100:
            break
        scaled = img.resize((w, h), PILImage.LANCZOS)
        buf = BytesIO()
        scaled.save(buf, format="JPEG", quality=80, optimize=True)
        if buf.tell() <= max_size:
            return buf.getvalue(), "image/jpeg"
        scale *= 0.75

    # Last resort: return whatever we have
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=30, optimize=True)
    return buf.getvalue(), "image/jpeg"


def encode_image(image_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_data, media_type)."""
    path = Path(image_path)
    if not path.exists():
        print(f"Error: file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    try:
        img_bytes, media_type = compress_image(image_path)
    except ImportError:
        # PIL not available, use raw
        if path.stat().st_size > 20 * 1024 * 1024:
            print(f"Error: file exceeds 20MB: {image_path}", file=sys.stderr)
            sys.exit(1)
        with open(path, "rb") as f:
            img_bytes = f.read()
        suffix = path.suffix.lower()
        media_type = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
        }.get(suffix, "image/png")

    return base64.b64encode(img_bytes).decode("utf-8"), media_type


def encode_image_from_url(image_url: str) -> tuple[str, str]:
    """Download an image from a URL and return (base64_data, media_type)."""
    session = create_session()
    try:
        resp = session.get(image_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.content
        if len(data) > 20 * 1024 * 1024:
            print("Error: image from URL exceeds 20MB", file=sys.stderr)
            sys.exit(1)
        ct = resp.headers.get("Content-Type", "").lower()
        media_type = ct if ct.startswith("image/") else "image/png"
        return base64.b64encode(data).decode("utf-8"), media_type
    except Exception as e:
        print(f"Error downloading image from URL: {e}", file=sys.stderr)
        sys.exit(1)


def extract_latest_session_image() -> str:
    """Extract the latest image from Claude Code session log. Returns file path."""
    log_dir = os.path.expanduser("~/.claude/projects/")
    if not os.path.isdir(log_dir):
        print("Error: Claude Code session log directory not found", file=sys.stderr)
        sys.exit(1)

    project_logs = list(Path(log_dir).rglob("*.jsonl"))
    if not project_logs:
        print("Error: no session logs found", file=sys.stderr)
        sys.exit(1)

    latest_log = max(project_logs, key=lambda p: p.stat().st_mtime)

    with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
        for line in reversed(f.readlines()):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                msg = data.get("message", {})
                if msg.get("role") != "user":
                    continue
                for item in msg.get("content", []):
                    if isinstance(item, dict) and item.get("type") == "image":
                        src = item.get("source", {})
                        img_data = src.get("data", "")
                        if img_data:
                            raw = base64.b64decode(img_data)
                            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
                            with open(CACHE_PATH, "wb") as fout:
                                fout.write(raw)
                            return str(CACHE_PATH)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    print("Error: no image found in session logs", file=sys.stderr)
    sys.exit(1)


def call_vision(api_key: str, b64_data: str, media_type: str, model: str, prompt: str) -> str:
    """Call Doubao vision API with connection pooling. Returns description text."""
    session = create_session()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{b64_data}"},
                    },
                ],
            }
        ],
        "max_tokens": 2000,
    }

    url = f"{API_BASE}/chat/completions"

    try:
        resp = session.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        body = e.response.text[:500]
        if status == 404 and "ModelNotOpen" in body and model != FALLBACK_MODEL:
            print(f"Model {model} not available, trying {FALLBACK_MODEL}...", file=sys.stderr)
            return call_vision(api_key, b64_data, media_type, FALLBACK_MODEL, prompt)
        print(f"API error ({status}): {body}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API call failed after retries: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Describe an image using Doubao vision")
    parser.add_argument("image", nargs="?", default=None,
                        help="Path to local image file, URL, or omit for --from-session")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--from-session", action="store_true",
                        help="Extract latest image from Claude Code conversation")
    parser.add_argument("-q", "--question", type=str, default=None,
                        help="Follow-up question about a previously described image (reuses cached image)")
    parser.add_argument("--prompt", default="请详细描述这张图片的内容，包括物体、人物、场景、文字、颜色、布局等。",
                        help="Custom prompt for image description")
    args = parser.parse_args()

    api_key = os.environ.get("DOUBAO_API_KEY")
    if not api_key:
        print("Error: DOUBAO_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    # Determine prompt: follow-up question overrides default prompt
    prompt = args.question if args.question else args.prompt

    # Resolve image source
    if args.from_session:
        if args.question and not args.image:
            # Follow-up: reuse cached image if it exists
            if CACHE_PATH.exists():
                img_path = str(CACHE_PATH)
            else:
                # No cache yet, extract from session
                img_path = extract_latest_session_image()
        else:
            img_path = extract_latest_session_image()
        b64, media_type = encode_image(img_path)
    elif args.image:
        if urlparse(args.image).scheme in ("http", "https"):
            b64, media_type = encode_image_from_url(args.image)
        else:
            b64, media_type = encode_image(args.image)
    else:
        print("Error: provide an image path or use --from-session", file=sys.stderr)
        sys.exit(1)

    result = call_vision(api_key, b64, media_type, args.model, prompt)
    print(result)


if __name__ == "__main__":
    main()
