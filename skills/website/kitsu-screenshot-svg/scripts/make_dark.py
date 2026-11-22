"""Build the dark version of a light Kitsu illustration SVG.

Usage: make_dark.py <light.svg> <dark.svg> [extra-map.json]
Colors come from kitsu/src/styles/theme.scss and the website dark.styl.
"""

import json
import re
import sys

# Fills and strokes of shapes: surfaces, stripes, borders.
SURFACES = {
    "#fff": "#36393f",
    "#ffffff": "#36393f",
    "#f8f8f8": "#3a3d43",
    "#f6f6f6": "#40444b",
    "#f4f4f4": "#40444b",
    "#f3f3f3": "#40444b",
    "#ececec": "#4e5159",
    "#e9e9e9": "#4e5159",
    "#e6e6e6": "#4e5159",
    "#e0e0e0": "#4e5159",
    "#dbdbdb": "#4e5159",
    "#363636": "#dcddde",
    "#8f91eb": "#9ea0fa",
}
# Text colors. White text sits on colored pills and stays white.
TEXT = {
    "#363636": "#dcddde",
    "#7a7a7a": "#eeeeee",
    "#000": "#fefefe",
    "#000000": "#fefefe",
}
# Kitsu dark theme status tags: colors.darkenColor (darken .3, saturate .6) of
# the default status colors; Todo turns #5F626A with white text.
STATUS = {
    "#22d160": "#00b738",
    "#ab26ff": "#8c00ff",
    "#ff3860": "#ff0005",
    "#3273dc": "#0045ca",
}
SURFACES.update(STATUS)
SURFACES["#ececec"] = "#5f626a"
TEXT.update(STATUS)
TEXT["#333"] = "#ffffff"
SHADOW = {"#363636": "#000000"}

COLOR_ATTR = re.compile(r'\b(fill|stroke|flood-color|stop-color)="(#[0-9a-fA-F]{3,6})"')
TAG = re.compile(r"<(svg|text|tspan|[a-zA-Z]+)\b[^>]*>")


def recolor(tag_match, extra, left):
    tag, name = tag_match.group(0), tag_match.group(1)
    table = TEXT if name in ("svg", "text", "tspan") else SURFACES

    def swap(m):
        attr, color = m.group(1), m.group(2).lower()
        mapping = {**(SHADOW if attr == "flood-color" else table), **extra}
        if color in mapping:
            return f'{attr}="{mapping[color]}"'
        left.add(color)
        return m.group(0)

    return COLOR_ATTR.sub(swap, tag)


def main():
    light, dark = sys.argv[1:3]
    extra = {k.lower(): v for k, v in json.load(open(sys.argv[3])).items()} if len(sys.argv) > 3 else {}
    svg = open(light).read()
    left = set()
    # Data URIs are long: skip <image> tags, they hold pixels, not colors.
    out = TAG.sub(lambda m: m.group(0) if m.group(1) == "image" else recolor(m, extra, left), svg)
    # Darker drop shadows read better on dark surfaces.
    out = re.sub(r'(flood-color="#000000" flood-opacity=")[.0-9]+"', r'\g<1>.45"', out)
    open(dark, "w").write(out)
    if left:
        print("colors left as is:", " ".join(sorted(left)))


if __name__ == "__main__":
    main()
