#!/usr/bin/env python3
"""Encode an image as base64 and ask a Qwen vision model about it."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-vl-max"
DEFAULT_TIMEOUT = 120

MIME_BY_SUFFIX = {
    ".avif": "image/avif",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


def load_config(config_path: Path) -> dict[str, Any]:
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    return {}


def mime_for_path(image_path: Path) -> str:
    return MIME_BY_SUFFIX.get(image_path.suffix.lower(), "application/octet-stream")


def build_data_uri(image_path: Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_for_path(image_path)};base64,{encoded}"


def build_payload(model: str, question: str, image_paths: list[Path]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": question}]
    for image_path in image_paths:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": build_data_uri(image_path)},
            }
        )
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }


def chat_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def call_vision_api(
    api_key: str,
    base_url: str,
    model: str,
    question: str,
    image_paths: list[Path],
    timeout: int,
) -> dict[str, Any]:
    payload = build_payload(model, question, image_paths)
    request = urllib.request.Request(
        chat_url(base_url),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_text(response: dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected API response shape: {json.dumps(response)[:500]}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a local image to a Qwen vision model and print its answer."
    )
    parser.add_argument("image", nargs="+", help="One or more local image file paths")
    parser.add_argument(
        "--question",
        default="Describe this image in detail, including any visible text.",
        help="Question or instruction for the vision model",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full API response as JSON instead of just the text",
    )
    parser.add_argument("--timeout", type=int, default=None, help="Request timeout in seconds")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    script_dir = Path(__file__).resolve().parent
    config = load_config(script_dir / "config.json")

    api_key = (
        os.environ.get("QWEN_VISION_API_KEY")
        or config.get("api_key")
        or ""
    ).strip()
    base_url = (
        os.environ.get("QWEN_VISION_BASE_URL")
        or config.get("base_url")
        or DEFAULT_BASE_URL
    ).strip()
    model = (
        os.environ.get("QWEN_VISION_MODEL")
        or config.get("model")
        or DEFAULT_MODEL
    ).strip()
    timeout = args.timeout or int(
        os.environ.get("QWEN_VISION_TIMEOUT") or DEFAULT_TIMEOUT
    )

    if not api_key:
        print(
            "Missing Qwen vision API key. Set QWEN_VISION_API_KEY or fill scripts/config.json.",
            file=sys.stderr,
        )
        return 2

    image_paths = [Path(path) for path in args.image]
    missing = [str(path) for path in image_paths if not path.is_file()]
    if missing:
        print(f"Image file not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    try:
        response = call_vision_api(
            api_key=api_key,
            base_url=base_url,
            model=model,
            question=args.question,
            image_paths=image_paths,
            timeout=timeout,
        )
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(
            f"Vision API error {error.code}: {body[:800]}",
            file=sys.stderr,
        )
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Vision API request failed: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(extract_text(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
