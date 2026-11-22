#!/usr/bin/env bash
# Render an SVG with headless Chrome (the only renderer here that handles
# feDropShadow and CSS animations). Usage: render.sh <file.svg> <out.png> [background]
set -euo pipefail
svg=$(realpath "$1")
out=$(realpath -m "$2")
bg=${3:-white}
html=$(mktemp --suffix=.html)
trap 'rm -f "$html"' EXIT
printf '<body style="margin:0;background:%s"><img src="file://%s" style="width:1100px;display:block">' "$bg" "$svg" > "$html"
google-chrome --headless=new --disable-gpu --allow-file-access-from-files \
  --hide-scrollbars --window-size=1100,1600 --screenshot="$out" "file://$html" 2>/dev/null
echo "$out"
