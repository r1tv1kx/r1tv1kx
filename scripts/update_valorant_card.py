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
    peak_rr_label = str(peak_rr) if peak_rr > 0 else "—"
    # Soft RR meter (subtle, not loud)
    fill = max(6, min(100, rr)) * 1.8
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="168" viewBox="0 0 520 168" role="img" aria-label="Valorant stats for {NAME}#{TAG}">
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#12171D"/>
      <stop offset="100%" stop-color="#0E1318"/>
    </linearGradient>
  </defs>

  <rect width="520" height="168" rx="10" fill="url(#card)"/>
  <rect x="0.5" y="0.5" width="519" height="167" rx="10" fill="none" stroke="#232A32" stroke-width="1"/>
  <rect x="0" y="18" width="3" height="132" fill="#FF4655" opacity="0.85"/>

  <text x="28" y="36" fill="#6B737C" font-family="Georgia, 'Times New Roman', serif" font-size="12" font-style="italic">valorant</text>
  <text x="492" y="36" text-anchor="end" fill="#9AA3AD" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="12">{NAME}#{TAG} · {REGION.upper()}</text>

  <text x="28" y="92" fill="#F2EDE6" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="36" font-weight="560" letter-spacing="-0.5">{rank}</text>
  <text x="492" y="78" text-anchor="end" fill="#6B737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11" letter-spacing="1">RR</text>
  <text x="492" y="112" text-anchor="end" fill="#F2EDE6" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="36" font-weight="560" letter-spacing="-0.5">{rr}</text>

  <rect x="28" y="108" width="180" height="2" rx="1" fill="#1C232B"/>
  <rect x="28" y="108" width="{fill:.1f}" height="2" rx="1" fill="#FF4655" opacity="0.7"/>

  <text x="28" y="148" fill="#6B737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="12">peak  <tspan fill="#D7DDE4" font-weight="600">{peak_rank}</tspan></text>
  <text x="492" y="148" text-anchor="end" fill="#6B737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="12">peak rr  <tspan fill="#D7DDE4" font-weight="600">{peak_rr_label}</tspan></text>
</svg>
'''


def main() -> None:
    rank, rr = fetch_mmr()
    peak_rank, peak_rr = resolve_peak(rank, rr)
    OUT.write_text(render(rank, rr, peak_rank, peak_rr), encoding="utf-8")
    print(f"Wrote {OUT} -> current {rank}/{rr} RR | peak {peak_rank}/{peak_rr} RR")


if __name__ == "__main__":
    main()
