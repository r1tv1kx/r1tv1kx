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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="240" viewBox="0 0 560 240" role="img" aria-label="Valorant stats for {NAME}#{TAG}">
  <defs>
    <linearGradient id="valoBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0F1923"/>
      <stop offset="55%" stop-color="#1C252E"/>
      <stop offset="100%" stop-color="#141A20"/>
    </linearGradient>
    <linearGradient id="valoRed" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FF4655"/>
      <stop offset="100%" stop-color="#FF6B77"/>
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1A242D"/>
      <stop offset="100%" stop-color="#152029"/>
    </linearGradient>
  </defs>

  <!-- clipped frame -->
  <path d="M0,16 L16,0 H544 L560,16 V224 L544,240 H16 L0,224 Z" fill="url(#valoBg)"/>
  <path d="M0,16 L16,0 H120 L104,16 Z" fill="url(#valoRed)"/>
  <path d="M560,16 L544,0 H480 L496,16 Z" fill="#FF4655" opacity="0.55"/>
  <path d="M8,24 H552 V216 H8 Z" fill="none" stroke="#2A3540" stroke-width="1"/>

  <text x="28" y="42" fill="#FF4655" font-family="Arial Black, Impact, sans-serif" font-size="13" letter-spacing="3">VALORANT</text>
  <text x="130" y="42" fill="#8B978F" font-family="Arial, Helvetica, sans-serif" font-size="13" letter-spacing="2">{REGION.upper()} // {NAME}#{TAG}</text>

  <!-- current panel -->
  <path d="M28,62 H268 L280,74 V148 L268,160 H28 L28,62 Z" fill="url(#panel)" stroke="#2F3B46"/>
  <text x="44" y="86" fill="#8B978F" font-family="Arial, Helvetica, sans-serif" font-size="12" letter-spacing="2">CURRENT RANK</text>
  <text x="44" y="132" fill="#FF4655" font-family="Arial Black, Impact, sans-serif" font-size="40">{rank.upper()}</text>

  <!-- rr panel -->
  <path d="M292,62 H532 L532,148 L520,160 H304 L292,148 Z" fill="url(#panel)" stroke="#2F3B46"/>
  <text x="312" y="86" fill="#8B978F" font-family="Arial, Helvetica, sans-serif" font-size="12" letter-spacing="2">RANK RATING</text>
  <text x="312" y="132" fill="#ECE8E1" font-family="Arial Black, Impact, sans-serif" font-size="40">{rr}</text>
  <text x="420" y="132" fill="#8B978F" font-family="Arial, Helvetica, sans-serif" font-size="16">RR</text>

  <!-- peak strip -->
  <path d="M28,176 H532 L532,208 L520,220 H40 L28,208 Z" fill="#FF4655" opacity="0.12" stroke="#FF4655" stroke-opacity="0.45"/>
  <text x="44" y="206" fill="#8B978F" font-family="Arial, Helvetica, sans-serif" font-size="12" letter-spacing="2">PEAK</text>
  <text x="100" y="208" fill="#ECE8E1" font-family="Arial Black, Impact, sans-serif" font-size="22">{peak_rank.upper()}</text>
  <text x="320" y="206" fill="#8B978F" font-family="Arial, Helvetica, sans-serif" font-size="12" letter-spacing="2">PEAK RR</text>
  <text x="400" y="208" fill="#FF4655" font-family="Arial Black, Impact, sans-serif" font-size="22">{peak_rr if peak_rr > 0 else '—'}</text>
</svg>
'''


def main() -> None:
    rank, rr = fetch_mmr()
    peak_rank, peak_rr = resolve_peak(rank, rr)
    OUT.write_text(render(rank, rr, peak_rank, peak_rr), encoding="utf-8")
    print(f"Wrote {OUT} -> current {rank}/{rr} RR | peak {peak_rank}/{peak_rr} RR")


if __name__ == "__main__":
    main()
