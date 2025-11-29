#!/usr/bin/env python3
"""
scripts/generate_thm_card.py

Fetch TryHackMe profile and render an SVG summary card using a Jinja2 SVG template.

Usage:
    python3 scripts/generate_thm_card.py --username ritviksingh --output tryhackme_card.svg

Dependencies:
    pip install requests jinja2

Notes:
- The script is defensive: missing values fall back to safe defaults (0 / "—").
- The script produces fields intended for an SVG template:
  username, rank_display, badges_display, rooms_display, streak_display,
  total_rooms (int), spark_points (polyline points), generated_at (UTC),
  card_w, card_h, progress_pct (0..100) which you can use to draw a progress arc.
"""

import argparse
import re
import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from datetime import datetime, timezone
import sys

def safe_int(s):
    """
    Convert a possibly noisy capture to an int.
    If s is None/empty or contains no digits, return 0.
    """
    if s is None:
        return 0
    s_clean = re.sub(r'[^\d]', '', str(s))
    return int(s_clean) if s_clean else 0


def extract_stats(html: str, username: str):
    """
    Best-effort extraction with safe fallbacks for each field.
    Returns a dict: { username, rank, badges, rooms, streak } (ints where applicable).
    """
    stats = {"username": username or "", "rank": 0, "badges": 0, "rooms": 0, "streak": 0}

    if not html:
        return stats

    # Rank (several heuristics)
    m = re.search(r'Rank[^0-9]{0,40}([0-9,]{1,9})', html, re.I)
    if m and m.group(1):
        stats["rank"] = safe_int(m.group(1))
    else:
        m2 = re.search(r'Rank.*?(\d{1,7})', html, re.I | re.S)
        if m2 and m2.group(1):
            stats["rank"] = safe_int(m2.group(1))

    # Badges
    m = re.search(r'Badges[^0-9]{0,40}([0-9]{1,4})', html, re.I)
    if m and m.group(1):
        stats["badges"] = safe_int(m.group(1))
    else:
        # fallback: look for a badge icon with adjacent number
        m2 = re.search(r'badge[s]?\W*[:\-\n\r ]+\s*([0-9]{1,4})', html, re.I)
        if m2 and m2.group(1):
            stats["badges"] = safe_int(m2.group(1))

    # Completed rooms
    m = re.search(r'Completed\s*rooms[^0-9]{0,50}([0-9,]{1,6})', html, re.I)
    if m and m.group(1):
        stats["rooms"] = safe_int(m.group(1))
    else:
        m2 = re.search(r'Completed[^0-9]{0,40}([0-9,]{1,6})', html, re.I)
        if m2 and m2.group(1):
            stats["rooms"] = safe_int(m2.group(1))
        else:
            # another heuristic for small profile pages
            m3 = re.search(r'Completed\s*:\s*([0-9,]{1,6})', html, re.I)
            if m3 and m3.group(1):
                stats["rooms"] = safe_int(m3.group(1))

    # Streak (optional)
    m = re.search(r'Streak[^0-9]{0,30}([0-9]{1,4})', html, re.I)
    if m and m.group(1):
        stats["streak"] = safe_int(m.group(1))

    # username fallback from URL if needed
    if not stats["username"]:
        m = re.search(r'/p/([A-Za-z0-9\-_]+)', html)
        if m and m.group(1):
            stats["username"] = m.group(1)

    # ensure ints
    stats["rank"] = int(stats["rank"]) if stats["rank"] else 0
    stats["badges"] = int(stats["badges"]) if stats["badges"] else 0
    stats["rooms"] = int(stats["rooms"]) if stats["rooms"] else 0
    stats["streak"] = int(stats["streak"]) if stats["streak"] else 0

    return stats


def synthesize_trend(total_rooms: int, points=12):
    """
    Create a simple, plausible trend array when historical data isn't available.
    Produces `points` integers ending at total_rooms.
    """
    points = max(2, int(points))
    if total_rooms <= 0:
        return [0] * points
    base = max(0, total_rooms - (points - 1))
    values = [base + i for i in range(points)]
    # scale to reach total_rooms exactly at the end
    if values[-1] != total_rooms and values[-1] != 0:
        scale = total_rooms / float(values[-1])
        values = [max(0, int(round(v * scale))) for v in values]
    # ensure non-decreasing monotonic trend
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            values[i] = values[i - 1]
    return values


def render_svg(template_path: Path, out_path: Path, context: dict):
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(['svg'])
    )
    tpl = env.get_template(template_path.name)
    svg = tpl.render(**context)
    out_path.write_text(svg, encoding='utf-8')
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")


def build_sparkline_points(values, width=360, height=44):
    """
    Convert a list of numeric values to a polyline point string for an SVG sparkline.
    values: list[int]
    returns "x1,y1 x2,y2 ..."
    """
    if not values:
        return ""
    maxv = max(values) if max(values) else 1
    norm = [v / maxv for v in values]
    pts = []
    n = len(norm)
    for i, v in enumerate(norm):
        x = int((i / (n - 1)) * width) if n > 1 else 0
        y = int((1 - v) * height)
        pts.append(f"{x},{y}")
    return " ".join(pts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--username', required=True, help='TryHackMe username (profile slug)')
    p.add_argument('--output', default='tryhackme_card.svg', help='Output SVG filename')
    p.add_argument('--template', default='templates/card_template.svg', help='Jinja2 SVG template path')
    p.add_argument('--points', default=12, type=int, help='Number of points to synthesize for sparkline')
    p.add_argument('--card-width', default=780, type=int, help='Card width (px) for template positioning')
    p.add_argument('--card-height', default=330, type=int, help='Card height (px) for template positioning')
    args = p.parse_args()

    username = args.username.strip()
    output_path = Path(args.output)
    template_path = Path(args.template)

    if not template_path.exists():
        print(f"Error: template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    profile_url = f"https://tryhackme.com/p/{username}"
    print(f"Fetching {profile_url}")

    html = ""
    try:
        r = requests.get(profile_url, timeout=15, headers={"User-Agent": "github-actions/1.0"})
        r.raise_for_status()
        html = r.text
    except requests.RequestException as e:
        print("Warning: failed to fetch profile page:", e)

    stats = extract_stats(html, username)
    if not stats.get("username"):
        stats["username"] = username

    # display strings
    stats["rank_display"] = f"{stats['rank']:,}" if stats["rank"] else "—"
    stats["badges_display"] = str(stats["badges"])
    stats["rooms_display"] = str(stats["rooms"])
    stats["streak_display"] = str(stats["streak"])
    stats["total_rooms"] = stats["rooms"]

    # Build trend (synthesized if no historical data)
    trend_values = synthesize_trend(stats["rooms"], points=args.points)
    spark_points = build_sparkline_points(trend_values, width=360, height=44)

    # Progress percentage: define a cap for visual progress (e.g., 100 rooms => 100%)
    # This is for showing a circular progress arc. Choose a sensible cap (e.g., 100 or 200).
    progress_cap = max(10, stats["rooms"], 100)  # avoid div-by-zero; min cap 100
    progress_pct = int(min(100, (stats["rooms"] / progress_cap) * 100))

    # timestamp (timezone-aware UTC)
    stats["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stats["spark_points"] = spark_points

    # layout fields (so template can align things)
    stats["card_w"] = args.card_width
    stats["card_h"] = args.card_height
    stats["progress_pct"] = progress_pct

    # Provide these top-level keys explicitly for template clarity
    context = {
        "username": stats["username"],
        "rank_display": stats["rank_display"],
        "badges_display": stats["badges_display"],
        "rooms_display": stats["rooms_display"],
        "streak_display": stats["streak_display"],
        "total_rooms": stats["total_rooms"],
        "spark_points": stats["spark_points"],
        "generated_at": stats["generated_at"],
        "card_w": stats["card_w"],
        "card_h": stats["card_h"],
        "progress_pct": stats["progress_pct"],
    }

    # Render template
    try:
        render_svg(template_path, output_path, context)
    except Exception as e:
        print("Error: failed to render SVG:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
