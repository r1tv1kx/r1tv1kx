#!/usr/bin/env python3
"""Fetch Valorant MMR and regenerate valorant_card.svg with peak tracking."""

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
PEAK_FILE = ROOT / "valorant_peak.json"

# Lowest -> highest. Used to keep lifetime peak without an official peak API.
RANK_ORDER = []
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


def load_peak() -> dict:
    if PEAK_FILE.exists():
        return json.loads(PEAK_FILE.read_text(encoding="utf-8"))
    return {}


def save_peak(peak_rank: str, peak_rr: int) -> None:
    PEAK_FILE.write_text(
        json.dumps({"peak_rank": peak_rank, "peak_rr": peak_rr}, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_peak(current_rank: str, current_rr: int) -> tuple[str, int]:
    peak = load_peak()
    peak_rank = peak.get("peak_rank", current_rank)
    peak_rr = int(peak.get("peak_rr", current_rr))
    if rank_score(current_rank, current_rr) > rank_score(peak_rank, peak_rr):
        peak_rank, peak_rr = current_rank, current_rr
    save_peak(peak_rank, peak_rr)
    return peak_rank, peak_rr


def render(rank: str, rr: int, peak_rank: str, peak_rr: int) -> str:
    # Competitive RR bar (0-100)
    bar_w = max(4, min(100, rr)) * 2.4  # up to 240px
    peak_rr_label = str(peak_rr) if peak_rr > 0 else "—"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="200" viewBox="0 0 560 200" role="img" aria-label="Valorant stats for {NAME}#{TAG}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0B1218"/>
      <stop offset="100%" stop-color="#151C24"/>
    </linearGradient>
    <linearGradient id="red" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FF4655"/>
      <stop offset="100%" stop-color="#FF6A75"/>
    </linearGradient>
    <linearGradient id="barTrack" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#1A222C"/>
      <stop offset="100%" stop-color="#222B36"/>
    </linearGradient>
  </defs>

  <!-- frame -->
  <rect width="560" height="200" rx="2" fill="url(#bg)"/>
  <path d="M0,0 H560 L548,12 H12 Z" fill="#FF4655" opacity="0.9"/>
  <rect x="1" y="1" width="558" height="198" rx="2" fill="none" stroke="#2A3340" stroke-width="1"/>

  <!-- identity -->
  <text x="28" y="44" fill="#7E8A94" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11" letter-spacing="3.5">VALORANT</text>
  <text x="118" y="44" fill="#4A5560" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11" letter-spacing="2">{REGION.upper()}</text>
  <text x="532" y="44" text-anchor="end" fill="#ECE8E1" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="13" font-weight="600" letter-spacing="0.5">{NAME}#{TAG}</text>

  <!-- divider -->
  <line x1="28" y1="58" x2="532" y2="58" stroke="#252D38" stroke-width="1"/>

  <!-- current -->
  <text x="28" y="86" fill="#7E8A94" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="10" letter-spacing="2.5">CURRENT</text>
  <text x="28" y="128" fill="#ECE8E1" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="42" font-weight="650">{rank}</text>

  <!-- rr -->
  <text x="320" y="86" fill="#7E8A94" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="10" letter-spacing="2.5">RR</text>
  <text x="320" y="128" fill="#FF4655" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="42" font-weight="650">{rr}</text>

  <!-- rr progress -->
  <rect x="320" y="140" width="240" height="3" rx="1.5" fill="url(#barTrack)"/>
  <rect x="320" y="140" width="{bar_w:.1f}" height="3" rx="1.5" fill="url(#red)"/>

  <!-- peak row -->
  <line x1="28" y1="162" x2="532" y2="162" stroke="#252D38" stroke-width="1"/>
  <text x="28" y="184" fill="#7E8A94" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="10" letter-spacing="2.5">PEAK</text>
  <text x="78" y="184" fill="#ECE8E1" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600">{peak_rank}</text>
  <text x="420" y="184" text-anchor="end" fill="#7E8A94" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="10" letter-spacing="2.5">PEAK RR</text>
  <text x="532" y="184" text-anchor="end" fill="#FF4655" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600">{peak_rr_label}</text>
</svg>
'''


def main() -> None:
    rank, rr = fetch_mmr()
    peak_rank, peak_rr = resolve_peak(rank, rr)
    OUT.write_text(render(rank, rr, peak_rank, peak_rr), encoding="utf-8")
    print(f"Wrote {OUT} -> current {rank}/{rr} RR | peak {peak_rank}/{peak_rr} RR")


if __name__ == "__main__":
    main()
