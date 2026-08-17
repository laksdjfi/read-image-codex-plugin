---
name: "read-image"
description: "Read, describe, OCR, or answer questions about local images by sending base64-encoded image data to a Qwen vision model."
---

# Read Image

## When To Use

- The user asks what an image contains, wants OCR text extracted, wants a screenshot explained, or asks any question about a local image file.
- The main model cannot see the image directly, or the image only exists as a local file path.

## Workflow

1. Confirm the image path exists and is a supported image format.
2. Run the bundled `read_image.py` script. It base64-encodes the image, sends it to the Qwen vision model configured in `scripts/config.json`, and prints the model's answer:

```bash
python "<read-image plugin scripts dir>/read_image.py" "<image path>" --question "<question>"
```

If the plugin install path is unknown, locate `read_image.py` by searching the `read-image` plugin source.
3. Return the script's stdout to the user as the image reading result. Do not invent content the script did not return.
4. If the script reports an HTTP or auth error, report the error to the user and check `scripts/config.json` for the API key, base URL, and model. Environment overrides `QWEN_VISION_API_KEY`, `QWEN_VISION_BASE_URL`, and `QWEN_VISION_MODEL` take precedence over the config file.

## Notes

- The default endpoint is OpenAI-compatible Qwen through DashScope compatible mode.
- Pass the user's actual question with `--question` so the vision model answers in the requested language and level of detail.
