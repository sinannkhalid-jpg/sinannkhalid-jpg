"""
make_info_card.py

Hand-authors info-card.svg: a neofetch-style panel (title bar + colored
key/value rows) that fades and slides in line by line, staggered, using
CSS @keyframes that live inside the SVG's own <style> tag (GitHub
sanitizes external/inline HTML style but renders <style> inside SVG).

Set STATIC=1 to emit a frozen (no-animation) frame for local previews.

Usage:
    python scripts/make_info_card.py
Output:
    info-card.svg
"""
import os
from pathlib import Path

# ---- Edit this block to personalize the card ----
DATA = {
    "now": "CSE and Cybersecurity Student",
    "prev": "Web Developer,Pentester",
    "os": "kali linux,Ubuntu,windows",
    "stack": "React, Next.js, TypeScript, Tailwind",
    "deploy": "Vercel, AWS EC2",
    "highlights": [
	"Built a OSINT, you can find in repo"
        "Built HallHub, a venue-booking PWA",
    ],
}
# ---------------------------------------------------

WIDTH = 490
LINE_H = 26
TITLE_H = 34
PAD_X = 18
FONT = "JetBrains Mono, SFMono-Regular, Consolas, monospace"
STAGGER = 0.12
DUR = 0.4

COLOR_KEY = "#39d353"
COLOR_VAL = "#c9d1d9"
COLOR_BG = "#0d1117"
COLOR_BORDER = "#30363d"
COLOR_TITLEBAR = "#161b22"
COLOR_DOT = ["#ff5f56", "#ffbd2e", "#27c93f"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_rows():
    rows = [
        ("now", DATA["now"]),
        ("prev", DATA["prev"]),
        ("os", DATA["os"]),
        ("stack", DATA["stack"]),
        ("deploy", DATA["deploy"]),
    ]
    return rows


def build_svg(static: bool) -> str:
    rows = build_rows()
    highlight_lines = DATA["highlights"]
    total_lines = len(rows) + 1 + len(highlight_lines)  # +1 blank/header spacer
    height = TITLE_H + (total_lines + 1) * LINE_H + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height:.0f}" viewBox="0 0 {WIDTH} {height:.0f}" '
        f'font-family="{FONT}" font-size="14">'
    )

    # keyframes (skipped entirely for static frame -> renders fully visible)
    if not static:
        parts.append(
            "<style>"
            "@keyframes lineIn {"
            "0% { opacity: 0; transform: translateX(-6px); }"
            "100% { opacity: 1; transform: translateX(0); }"
            "}"
            ".line { opacity: 0; animation: lineIn 0.01s linear forwards; }"
            "</style>"
        )

    # card background + border
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1:.0f}" '
        f'rx="8" fill="{COLOR_BG}" stroke="{COLOR_BORDER}"/>'
    )
    # title bar
    parts.append(f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{TITLE_H}" rx="8" fill="{COLOR_TITLEBAR}"/>')
    parts.append(f'<rect x="0.5" y="{TITLE_H-8:.0f}" width="{WIDTH-1}" height="8" fill="{COLOR_TITLEBAR}"/>')
    for i, dot in enumerate(COLOR_DOT):
        parts.append(f'<circle cx="{16 + i*18}" cy="{TITLE_H/2:.0f}" r="5" fill="{dot}"/>')
    parts.append(
        f'<text x="{WIDTH/2:.0f}" y="{TITLE_H/2+5:.0f}" text-anchor="middle" '
        f'fill="#8b949e" font-size="12">avi@github: ~/whoami</text>'
    )

    y = TITLE_H + LINE_H
    line_idx = 0

    def anim_attrs(idx):
        if static:
            return ""
        begin = idx * STAGGER
        return f' style="animation-delay:{begin:.2f}s; animation-duration:{DUR}s;"'

    for key, val in rows:
        cls = "" if static else ' class="line"'
        parts.append(
            f'<text x="{PAD_X}" y="{y}"{cls}{anim_attrs(line_idx)}>'
            f'<tspan fill="{COLOR_KEY}">{esc(key)}</tspan>'
            f'<tspan fill="{COLOR_VAL}">  {esc(val)}</tspan>'
            f"</text>"
        )
        y += LINE_H
        line_idx += 1

    y += LINE_H * 0.3
    cls = "" if static else ' class="line"'
    parts.append(
        f'<text x="{PAD_X}" y="{y}"{cls}{anim_attrs(line_idx)} fill="{COLOR_KEY}">highlights</text>'
    )
    y += LINE_H
    line_idx += 1
    for h in highlight_lines:
        cls = "" if static else ' class="line"'
        parts.append(
            f'<text x="{PAD_X}" y="{y}"{cls}{anim_attrs(line_idx)}>'
            f'<tspan fill="{COLOR_VAL}">- {esc(h)}</tspan>'
            f"</text>"
        )
        y += LINE_H
        line_idx += 1

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static)
    Path("info-card.svg").write_text(svg)
    print("Wrote info-card.svg" + (" (static)" if static else ""))
