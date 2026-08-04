"""
make_ascii_svg.py

Converts source-prepped.png into avi-ascii.svg: a monochrome ASCII
portrait that "types" itself in row by row using SMIL clip-path wipes.
No JS, no external CSS -- everything lives inside the SVG so GitHub
will render and animate it.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png]
Output:
    avi-ascii.svg
"""
import sys
from pathlib import Path

from PIL import Image

# leading space clears background -> nothing prints there.
# bright (sparse) -> dark (dense)
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53
FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE * 1.0
FILL_COLOR = "#8b949e"  # single light-gray fill, no rainbow per-char color
ROW_STAGGER = 0.085     # seconds between each row starting to wipe in
WIPE_DURATION = 0.55    # seconds for a single row to wipe fully in


def image_to_ascii_rows(img_path: str, cols: int = COLS, rows: int = ROWS):
    img = Image.open(img_path).convert("L")
    src_w, src_h = img.size
    char_aspect = CHAR_W / CHAR_H
    target_ratio = (cols * char_aspect) / rows
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    img = img.resize((cols, rows))
    pixels = list(img.getdata())

    ramp_len = len(RAMP)
    ascii_rows = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]  # 0=black .. 255=white
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            row_chars.append(RAMP[idx])
        ascii_rows.append("".join(row_chars))
    return ascii_rows


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(ascii_rows, out_path: str):
    width = COLS * CHAR_W
    height = ROWS * CHAR_H

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" font-family="JetBrains Mono, '
        f'SFMono-Regular, Consolas, monospace" font-size="{FONT_SIZE}">'
    )
    parts.append(
        f'<rect width="100%" height="100%" fill="#0d1117" rx="6"/>'
    )
    parts.append("<defs>")

    for i, row in enumerate(ascii_rows):
        y = (i + 1) * CHAR_H
        clip_id = f"clip-row-{i}"
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'  <rect x="0" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">'
        )
        begin = i * ROW_STAGGER
        parts.append(
            f'    <animate attributeName="width" from="0" to="{width:.0f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DURATION}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>'
        )
        parts.append("  </rect>")
        parts.append("</clipPath>")

    parts.append("</defs>")

    for i, row in enumerate(ascii_rows):
        y = (i + 1) * CHAR_H
        clip_id = f"clip-row-{i}"
        safe_row = esc(row)
        parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{y - 1.5:.1f}" fill="{FILL_COLOR}" '
            f'xml:space="preserve">{safe_row}</text>'
            f"</g>"
        )
        begin = i * ROW_STAGGER
        parts.append(
            f'<rect y="{y - CHAR_H:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" '
            f'fill="{FILL_COLOR}" opacity="0.9">'
            f'<animate attributeName="x" from="0" to="{width - CHAR_W:.0f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DURATION}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0 0.2 1"/>'
            f'<animate attributeName="opacity" values="0.9;0.9;0" '
            f'begin="{begin:.3f}s" dur="{WIPE_DURATION + 0.05}s" fill="freeze"/>'
            f"</rect>"
        )

    parts.append("</svg>")
    Path(out_path).write_text("\n".join(parts))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    rows = image_to_ascii_rows(src)
    build_svg(rows, "avi-ascii.svg")
