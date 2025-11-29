#!/usr/bin/env python3
"""
Fetch TryHackMe profile and render an SVG summary card.
Dependencies: requests, jinja2
Usage: python generate_thm_card.py --username ritviksingh --output tryhackme_card.svg
"""

import argparse
import re
import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

def safe_int(s):
    if not s:
        return 0
    return int(re.sub(r'[^\d]', '', s))

def extract_stats(html: str):
    # Try several heuristics and fallbacks to find numeric stats.
    # rank, badges, completed rooms, streak (optional), username.
    result = {"rank": 0, "badges": 0, "rooms": 0, "streak": 0, "username": ""}

    # Username (profile header)
    m = re.search(r'profile.*?username.*?>([\w\-\_]+)<', html, re.I|re.S)
    if not m:
        # fallback: look for the page title or header text
        m = re.search(r'>([A-Za-z0-9\-_]{3,30})\s*\[', html)
    if m:
        result["username"] = m.group(1)

    # Rank — look for 'Rank' label nearby a number
    m = re.search(r'Rank[^0-9]{0,40}([0-9,]{1,9})', html, re.I)
    if m:
        result["rank"] = safe_int(m.group(1))
    else:
        # alternate: trophy icon column
        m = re.search(r'Rank.*?(\d{1,7})', html, re.I|re.S)
        if m:
            result["rank"] = safe_int(m.group(1))

    # Badges — look for 'Badges' label nearby a number
    m = re.search(r'Badges[^0-9]{0,40}([0-9]{1,4})', html, re.I)
    if m:
        result["badges"] = safe_int(m.group(1))

    # Completed rooms — look for 'Completed rooms' or 'Completed' label
    m = re.search(r'Completed\s*rooms[^0-9]{0,50}([0-9,]{1,6})', html, re.I)
    if m:
        result["rooms"] = safe_int(m.group(1))
    else:
        m = re.search(r'Completed[^0-9]{0,40}([0-9,]{1,6})', html, re.I)
        if m:
            result["rooms"] = safe_int(m.group(1))

    # Streak (if available)
    m = re.search(r'Streak[^0-9]{0,30}([0-9]{1,4})', html, re.I)
    if m:
        result["streak"] = safe_int(m.group(1))

    # If nothing parsed for username, attempt to pull from canonical URL
    if not result["username"]:
        m = re.search(r'/p/([A-Za-z0-9\-_]+)', html)
        if m:
            result["username"] = m.group(1)

    return result

def render_svg(template_path: Path, out_path: Path, context: dict):
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(['svg'])
    )
    tpl = env.get_template(template_path.name)
    svg = tpl.render(**context)
    out_path.write_text(svg, encoding='utf-8')
    print(f"Wrote {out_path} (size: {out_path.stat().st_size} bytes)")

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--username', required=True)
    p.add_argument('--output', default='tryhackme_card.svg')
    p.add_argument('--template', default='templates/card_template.svg')
    args = p.parse_args()

    profile_url = f"https://tryhackme.com/p/{args.username}"
    print(f"Fetching {profile_url}")
    try:
        r = requests.get(profile_url, timeout=15)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("Failed to fetch profile:", e)
        html = ""

    stats = extract_stats(html)
    # ensure username present
    stats.setdefault("username", args.username)

    # fill some display-friendly fields
    stats["rank_display"] = f"{stats['rank']:,}" if stats["rank"] else "—"
    stats["badges_display"] = str(stats["badges"])
    stats["rooms_display"] = str(stats["rooms"])
    stats["streak_display"] = str(stats["streak"])

    # generate card
    template_path = Path(args.template)
    out_path = Path(args.output)
    render_svg(template_path, out_path, stats)

if __name__ == '__main__':
    main()
