#!/usr/bin/env python3
# fieldscan.py
# Point this at a site photo and it drafts a defect description, category,
# severity, and spec section instead of typing it by hand. Used Claude to help
# scaffold this and clean up the vision prompt.
#
# setup:
#   pip install anthropic
#   export ANTHROPIC_API_KEY=...
#   python fieldscan.py sample_site_photo.jpg
#
# no key set -> prints example output instead of pretending to analyze the photo

import base64
import json
import os
import sys
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

EXAMPLE_OUTPUT = {
    "description": "Vertical crack running approximately 18 inches up the interior "
                    "drywall, widening slightly near the base, consistent with "
                    "settling or moisture related movement.",
    "category": "Structural / Drywall",
    "severity": "Medium — monitor and schedule repair within 30 days",
    "suggested_spec_section": "CSI 09 29 00 — Gypsum Board",
    "confidence_note": "Recommend a licensed structural inspector confirm severity "
                        "before scheduling repair crews.",
}


class UnsupportedImageError(Exception):
    pass


def detect_image_media_type(img_bytes: bytes, image_path: str) -> str:
    # check actual file bytes, not the extension. downloaded files are wrong
    # about this constantly (avif saved as .png, etc), used to blow up with a
    # raw API error before this existed
    if img_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if img_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if img_bytes[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
        return "image/webp"

    raise UnsupportedImageError(
        f"'{image_path}' isn't actually a jpeg/png/gif/webp, probably an avif or "
        f"heic saved with the wrong extension. convert it and try again."
    )


def analyze_photo(image_path: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    img_bytes = Path(image_path).read_bytes()
    media_type = detect_image_media_type(img_bytes, image_path)
    b64_image = base64.standard_b64encode(img_bytes).decode("utf-8")

    prompt = """You are a field inspection assistant for architecture, engineering,
and construction site visits. Look at this site photo and draft a professional
observation entry a human inspector would review and confirm.

Respond ONLY as JSON with these exact keys:
{
  "description": "<2-3 sentence professional description of what you observe>",
  "category": "<short defect category, e.g. Structural, Electrical, Safety, Finish Work>",
  "severity": "<Low, Medium, or High, with a one-clause reason>",
  "suggested_spec_section": "<a plausible CSI MasterFormat section if applicable, or 'N/A'>",
  "confidence_note": "<one sentence noting any uncertainty or need for expert confirmation>"
}

If the photo doesn't show a clear defect, say so honestly in the description
rather than inventing one."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64_image},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    text = response.content[0].text.strip().strip("`").replace("json\n", "")
    return json.loads(text)


def main():
    if len(sys.argv) < 2:
        print("Usage: python fieldscan.py <path_to_site_photo.jpg>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not ANTHROPIC_API_KEY:
        print("[NO API KEY SET]")
        print("This is NOT an analysis of your photo. It's an example of the output")
        print("shape you'll get once ANTHROPIC_API_KEY is set:\n")
        print(json.dumps(EXAMPLE_OUTPUT, indent=2))
        print("\nSet ANTHROPIC_API_KEY and re-run to analyze the actual photo.")
        return

    print(f"Analyzing {image_path} ...\n")
    try:
        result = analyze_photo(image_path)
    except UnsupportedImageError as e:
        print(f"[UNSUPPORTED IMAGE] {e}")
        return
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
