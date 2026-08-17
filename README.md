# read-image

Codex plugin that reads local images with a Qwen vision model.

## How It Works

1. `scripts/read_image.py` reads the image file and encodes it as base64.
2. The base64 image is sent as a data URI to the configured Qwen vision model.
3. The vision model's answer is printed to stdout and returned to the main Codex model.

## Usage

```bash
python scripts/read_image.py "C:\path\to\image.png" --question "What does this image show?"
```

Pass multiple images by adding more paths:

```bash
python scripts/read_image.py "a.png" "b.png" --question "Compare these two screenshots."
```

## Configuration

Default settings live in `scripts/config.json`:

- `api_key`: Qwen vision API key
- `base_url`: OpenAI-compatible API base URL
- `model`: Qwen vision model name

Environment variables override the config file:

- `QWEN_VISION_API_KEY`
- `QWEN_VISION_BASE_URL`
- `QWEN_VISION_MODEL`
- `QWEN_VISION_TIMEOUT`

The API key is stored in this local plugin so it works after installation. Do not share the plugin directory or commit `scripts/config.json` to a public repository.
