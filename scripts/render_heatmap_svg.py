"""
render_heatmap_svg.py

Reads data/contributions.json and draws the classic 53-week x 7-day
contribution calendar as rounded boxes, revealed once with a diagonal
slide-down (CSS keyframes, plays on load, freezes -- no looping).

Usage:
    python scripts/render_heatmap_svg.py
Output:
    contrib-heatmap.svg
"""
import json
from datetime import datetime
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# index 0 = none, 5 = brightest (neon top end, brighter than GitHub's own max)

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 30
TOP_PAD = 40
BOTTOM_PAD = 46
FONT = "JetBrains Mono, SFMono-Regular, Consolas, monospace"

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def level_for(count: int, thresholds=(0, 2, 5, 10, 20)) -> int:
    # thresholds map count -> palette index 0..5
    for i, t in enumerate(thresholds):
        if count <= t:
            return i
    return len(thresholds)


def build_weeks(days):
    """Group days into weeks (columns), Sunday-first, matching GitHub layout."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []

    first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    # rewind to the preceding Sunday so week columns align
    start_offset = (first.weekday() + 1) % 7  # weekday(): Mon=0 .. Sun=6
    weeks = []
    cur_week = [None] * start_offset
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        level = d["level"] if d["level"] is not None else level_for(d["count"])
        cur_week.append({"date": d["date"], "count": d["count"], "level": level, "dt": dt})
        if dt.weekday() == 5:  # Saturday -> close week
            weeks.append(cur_week)
            cur_week = []
    if cur_week:
        while len(cur_week) < 7:
            cur_week.append(None)
        weeks.append(cur_week)
    return weeks


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(payload: dict, out_path: str):
    days = payload["days"]
    stats = payload["stats"]
    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * CELL + 10
    height = TOP_PAD + 7 * CELL + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="{FONT}" font-size="10">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="#0d1117" rx="6"/>')
    parts.append(
        "<style>"
        "@keyframes boxIn {"
        "0% { opacity: 0; transform: translateY(-4px); }"
        "100% { opacity: 1; transform: translateY(0); }"
        "}"
        ".box { opacity: 0; animation: boxIn 0.01s linear forwards; transform-box: fill-box; }"
        "</style>"
    )

    # month labels (approximate: label the week column where the month changes)
    last_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            m = day["dt"].month
            if m != last_month:
                x = LEFT_PAD + wi * CELL
                parts.append(
                    f'<text x="{x}" y="16" fill="#8b949e">{MONTH_LABELS[m-1]}</text>'
                )
                last_month = m
            break

    # day-of-week labels
    for row, label in DAY_LABELS.items():
        y = TOP_PAD + row * CELL + BOX - 2
        parts.append(f'<text x="0" y="{y}" fill="#8b949e">{label}</text>')

    # boxes: diagonal stagger by (week + row)
    max_diag = n_weeks + 7
    for wi, week in enumerate(weeks):
        for ri, day in enumerate(week):
            if day is None:
                continue
            level = max(0, min(5, day["level"]))
            color = PALETTE[level]
            x = LEFT_PAD + wi * CELL
            y = TOP_PAD + ri * CELL
            diag = wi + ri
            delay = (diag / max_diag) * 2.6  # spread the whole reveal over ~1.6s
            title = f'{day["count"]} contributions on {day["date"]}'
            parts.append(
                f'<rect class="box" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'rx="2" fill="{color}" style="animation-delay:{delay:.3f}s; '
                f'animation-duration:0.55s;">'
                f'<title>{esc(title)}</title>'
                f"</rect>"
            )

    # legend
    legend_y = TOP_PAD + 7 * CELL + 20
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y}" fill="#8b949e">Less</text>')
    lx = LEFT_PAD + 34
    for level, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx}" y="{legend_y-9}" width="{BOX}" height="{BOX}" rx="2" fill="{color}"/>'
        )
        lx += CELL
    parts.append(f'<text x="{lx+4}" y="{legend_y}" fill="#8b949e">More</text>')

    # stats footer
    footer = f'{stats["total"]:,} contributions in the last year'
    parts.append(
        f'<text x="{width - 10:.0f}" y="{legend_y}" text-anchor="end" '
        f'fill="#c9d1d9">{esc(footer)}</text>'
    )

    parts.append("</svg>")
    Path(out_path).write_text("\n".join(parts))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    payload = json.loads(Path("data/contributions.json").read_text())
    build_svg(payload, "contrib-heatmap.svg")
