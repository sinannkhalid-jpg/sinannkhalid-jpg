"""
fetch_contributions.py

Fetches your public contribution calendar from
https://github.com/users/<username>/contributions -- the same HTML
fragment GitHub's own profile page uses -- with no GraphQL API and
no personal access token required.

Usage:
    python scripts/fetch_contributions.py [username]
Output:
    data/contributions.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "sinannkhalid-jpg"
URL_TMPL = "https://github.com/users/{username}/contributions"


def fetch_calendar(username: str):
    resp = requests.get(
        URL_TMPL.format(username=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-art-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    # GitHub renders each day as a <td> with data-date / data-level,
    # or (older markup) as <rect> with data-date/data-count.
    cells = soup.select("td.ContributionCalendar-day, td[data-date]")
    if not cells:
        cells = soup.select("rect.ContributionCalendar-day, rect[data-date]")

    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue
        level = cell.get("data-level")
        count = cell.get("data-count")
        tooltip_id = cell.get("id")
        tip_text = None
        if tooltip_id:
            tip = soup.find(attrs={"for": tooltip_id}) or soup.find(
                "tool-tip", attrs={"for": tooltip_id}
            )
            if tip:
                tip_text = tip.get_text(strip=True)

        if count is None and tip_text:
            digits = "".join(ch for ch in tip_text.split(" ")[0] if ch.isdigit())
            count = digits or "0"

        days.append(
            {
                "date": date,
                "level": int(level) if level is not None else None,
                "count": int(count) if count else 0,
            }
        )

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    # current streak: consecutive days with count > 0 ending today (or last day with data)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": monthly,
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    days = fetch_calendar(username)
    if not days:
        print(
            "No contribution cells found. GitHub may have changed its HTML "
            "structure, or the profile is private.",
            file=sys.stderr,
        )
        sys.exit(1)

    stats = compute_stats(days)
    out = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    Path("data").mkdir(exist_ok=True)
    Path("data/contributions.json").write_text(json.dumps(out, indent=2))
    print(f"Wrote data/contributions.json ({stats['total']} contributions found)")
