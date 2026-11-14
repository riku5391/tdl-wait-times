#!/usr/bin/env python3
"""Build a self-contained HTML from existing repository JPG assets. No network required."""
import base64, json, re, sys
from pathlib import Path

def build(source, assets, output):
    html=Path(source).read_text(encoding="utf-8")
    photos={}
    for path in sorted(Path(assets).glob("ride-*.jpg")):
        raw=path.read_bytes()
        if not raw.startswith(bytes.fromhex("ffd8ff")):
            raise ValueError(f"Invalid JPEG: {path}")
        photos[path.name]="data:image/jpeg;base64,"+base64.b64encode(raw).decode("ascii")
    if not photos:
        raise ValueError("No ride-*.jpg files found in assets directory")
    payload="<script id=\"tdl-embedded-photos\">window.__TDL_EMBEDDED_PHOTOS="+json.dumps(photos,separators=(",",":"))+";</script>"
    html=html.replace("</head>",payload+"</head>",1)
    if "window.__TDL_EMBEDDED_PHOTOS" not in html:
        raise ValueError("Embedded photo hook missing")
    Path(output).write_text(html,encoding="utf-8")
    return len(photos),len(html)

if __name__=="__main__":
    if len(sys.argv)!=4:
        sys.exit("Usage: python build_offline.py SOURCE_HTML ASSETS_DIR OUTPUT_HTML")
    count,size=build(*sys.argv[1:])
    print(f"Embedded {count} JPEG photos; output {size:,} bytes")
