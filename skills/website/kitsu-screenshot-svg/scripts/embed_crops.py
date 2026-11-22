"""Replace placeholder <symbol>s of an SVG with crops of the original screenshot.

Usage: embed_crops.py <draft.svg> <original.png> <crops.json> <out.svg>
crops.json: {"symbol-id": [x, y, w, h], ...}, boxes in pixels of the PNG.
"""

import base64
import json
import re
import subprocess
import sys


def crop(png, x, y, w, h):
    data = subprocess.run(
        ["convert", png, "-crop", f"{w}x{h}+{x}+{y}", "+repage", "-strip", "png:-"],
        capture_output=True,
        check=True,
    ).stdout
    return "data:image/png;base64," + base64.b64encode(data).decode()


def embed(svg, symbol_id, uri):
    pattern = re.compile(
        r'<symbol id="%s"([^>]*)>(.*?)</symbol>' % re.escape(symbol_id), re.S
    )
    match = pattern.search(svg)
    if not match:
        sys.exit(f"symbol not found: {symbol_id}")
    attrs, body = match.groups()
    view_box = re.search(r'viewBox="([^"]+)"', attrs)
    if not view_box:
        sys.exit(f"symbol without viewBox: {symbol_id}")
    _, _, w, h = view_box.group(1).split()
    image = f'<image href="{uri}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/>'
    clip = re.search(r'clip-path="url\(#([^)]+)\)"', body)
    if clip:
        image = f'<g clip-path="url(#{clip.group(1)})">{image}</g>'
    return svg[: match.start()] + f'<symbol id="{symbol_id}"{attrs}>{image}</symbol>' + svg[match.end() :]


def main():
    draft, png, crops_path, out = sys.argv[1:5]
    svg = open(draft).read()
    for symbol_id, box in json.load(open(crops_path)).items():
        svg = embed(svg, symbol_id, crop(png, *box))
    open(out, "w").write(svg)


if __name__ == "__main__":
    main()
