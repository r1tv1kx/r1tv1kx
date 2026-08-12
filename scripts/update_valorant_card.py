#!/usr/bin/env python3
"""Fetch live Valorant MMR and render an elegant stats card."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

NAME = "GunmaN"
TAG = "1803"
REGION = "ap"
API = f"https://api.kyroskoh.xyz/valorant/v1/mmr/{REGION}/{NAME}/{TAG}"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "valorant_card.svg"
STATS_FILE = ROOT / "valorant_stats.json"
PEAK_FILE = ROOT / "valorant_peak.json"

FONT = "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"

RANK_ORDER: list[str] = []
for tier in (
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Diamond",
    "Ascendant",
    "Immortal",
):
    for div in (3, 2, 1):
        RANK_ORDER.append(f"{tier} {div}")
RANK_ORDER.append("Radiant")
RANK_INDEX = {name.lower(): i for i, name in enumerate(RANK_ORDER)}


def rank_score(rank: str, rr: int) -> tuple[int, int]:
    return RANK_INDEX.get(rank.lower(), -1), rr


def fetch_mmr() -> tuple[str, int]:
    req = urllib.request.Request(
        API,
        headers={
            "User-Agent": "r1tv1kx-profile-readme/1.0",
            "Accept": "text/plain",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8").strip()
    m = re.match(r"^(.+?)\s*-\s*(\d+)\s*RR$", text, re.I)
    if not m:
        raise SystemExit(f"Unexpected MMR payload: {text!r}")
    return m.group(1).strip(), int(m.group(2))


def load_json(path: Path, default: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return dict(default)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def resolve_peak(stats: dict, current_rank: str, current_rr: int) -> tuple[str, str]:
    peak = load_json(PEAK_FILE, {})
    peak_rank = peak.get("peak_rank") or stats.get("peak_rank") or current_rank
    peak_rr = int(peak.get("peak_rr", stats.get("peak_rr", 0)) or 0)
    peak_act = peak.get("peak_act") or stats.get("peak_act") or ""

    if rank_score(current_rank, current_rr) > rank_score(peak_rank, peak_rr):
        peak_rank, peak_rr = current_rank, current_rr

    save_json(
        PEAK_FILE,
        {"peak_rank": peak_rank, "peak_rr": peak_rr, "peak_act": peak_act},
    )
    return peak_rank, peak_act


def fmt_int(n: int) -> str:
    return f"{n:,}"


def text(
    x: float,
    y: float,
    content: object,
    *,
    fill: str,
    size: int,
    weight: str | None = None,
    anchor: str | None = None,
    tracking: str | None = None,
) -> str:
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'fill="{fill}"',
        f'font-family="{FONT}"',
        f'font-size="{size}"',
    ]
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if tracking:
        attrs.append(f'letter-spacing="{tracking}"')
    return f"  <text {' '.join(attrs)}>{content}</text>"


def metric(x: float, label_y: float, value_y: float, label: str, value: object) -> str:
    return "\n".join(
        [
            text(x, label_y, label, fill="#6A737C", size=11),
            text(x, value_y, value, fill="#F4F0EA", size=20, weight="600"),
        ]
    )


def render(rank: str, rr: int, peak_rank: str, peak_act: str, s: dict) -> str:
    w, h = 720, 430
    agents = s.get("agents") or []
    premier = s.get("premier", "")
    ddelta = int(s.get("ddelta", 0))
    ddelta_s = f"+{ddelta}" if ddelta > 0 else str(ddelta)

    hero = [
        ("dmg/r", s["adr"]),
        ("k/d", s["kd"]),
        ("hs%", s["hs"]),
        ("win%", s["win_pct"]),
        ("acs", s["acs"]),
    ]
    row_a = [
        ("kast", s["kast"]),
        ("ddΔ", ddelta_s),
        ("kad", s["kad"]),
        ("k/r", s["kpr"]),
        ("1v1", fmt_int(int(s["clutches"]))),
        ("flawless", fmt_int(int(s["flawless"]))),
    ]
    row_b = [
        ("kills", fmt_int(int(s["kills"]))),
        ("deaths", fmt_int(int(s["deaths"]))),
        ("assists", fmt_int(int(s["assists"]))),
    ]

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Valorant stats for {NAME}#{TAG}">',
        "  <defs>",
        '    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '      <stop offset="0%" stop-color="#0C1014"/>',
        '      <stop offset="100%" stop-color="#12181F"/>',
        "    </linearGradient>",
        "  </defs>",
        "",
        f'  <rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>',
        f'  <rect x="0.6" y="0.6" width="{w - 1.2}" height="{h - 1.2}" rx="12" fill="none" stroke="#1E262E" stroke-width="1"/>',
        '  <circle cx="24" cy="28" r="3" fill="#FF4655"/>',
        "",
        text(38, 32, "valorant · competitive", fill="#8A939C", size=12, tracking="0.4"),
        text(w - 24, 32, f"{NAME}#{TAG}", fill="#D8DEE5", size=13, weight="600", anchor="end"),
        "",
        text(28, 82, rank, fill="#F4F0EA", size=34, weight="600", tracking="-0.6"),
        text(200, 82, rr, fill="#FF4655", size=34, weight="600", tracking="-0.6"),
        text(268, 82, "rr", fill="#6A737C", size=13),
        "",
        text(w - 24, 66, "peak", fill="#6A737C", size=11, anchor="end"),
        text(w - 24, 88, peak_rank, fill="#D8DEE5", size=16, weight="600", anchor="end"),
        text(w - 24, 106, peak_act, fill="#6A737C", size=11, anchor="end"),
        "",
        f'  <line x1="28" y1="122" x2="{w - 28}" y2="122" stroke="#1C242C" stroke-width="1"/>',
        "",
    ]

    for i, (label, value) in enumerate(hero):
        parts.append(metric(28 + i * 92, 148, 172, label, value))

    parts.extend(
        [
            text(w - 24, 148, "record", fill="#6A737C", size=11, anchor="end"),
            text(
                w - 24,
                172,
                f"{fmt_int(int(s['wins']))}W · {fmt_int(int(s['losses']))}L",
                fill="#F4F0EA",
                size=16,
                weight="600",
                anchor="end",
            ),
            "",
            f'  <line x1="28" y1="192" x2="{w - 28}" y2="192" stroke="#1C242C" stroke-width="1"/>',
            "",
        ]
    )

    for i, (label, value) in enumerate(row_a):
        parts.append(metric(28 + i * 112, 218, 240, label, value))

    for i, (label, value) in enumerate(row_b):
        parts.append(metric(28 + i * 140, 268, 290, label, value))

    parts.extend(
        [
            "",
            f'  <line x1="28" y1="308" x2="{w - 28}" y2="308" stroke="#1C242C" stroke-width="1"/>',
            "",
            text(28, 330, "top agents", fill="#6A737C", size=11, tracking="0.3"),
            "",
        ]
    )

    for i, agent in enumerate(agents[:3]):
        y = 354 + i * 20
        name = agent["name"]
        detail = (
            f"{agent['hours']}h · {fmt_int(int(agent['matches']))}  ·  "
            f"{agent['win_pct']}% wr  ·  {float(agent['kd']):.2f} kd  ·  "
            f"{agent['best_map']} {agent['best_map_wr']}%"
        )
        parts.append(text(28, y, name, fill="#D8DEE5", size=13, weight="600"))
        parts.append(text(100, y, detail, fill="#8A939C", size=12))

    footer = (
        f"lvl {int(s['level'])}  ·  {fmt_int(int(s['hours']))}h  ·  "
        f"{fmt_int(int(s['matches']))} matches"
    )
    if premier:
        footer += f"  ·  {premier}"

    parts.extend(
        [
            "",
            text(28, h - 16, footer, fill="#5A636C", size=11),
            "</svg>",
            "",
        ]
    )
    return "\n".join(parts)


def main() -> None:
    stats = load_json(STATS_FILE, {})
    if not stats:
        raise SystemExit(f"Missing stats file: {STATS_FILE}")

    rank, rr = fetch_mmr()
    peak_rank, peak_act = resolve_peak(stats, rank, rr)
    OUT.write_text(render(rank, rr, peak_rank, peak_act, stats), encoding="utf-8")
    print(
        f"Wrote {OUT} -> {rank}/{rr} RR | peak {peak_rank}"
        + (f" ({peak_act})" if peak_act else "")
    )


if __name__ == "__main__":
    main()
