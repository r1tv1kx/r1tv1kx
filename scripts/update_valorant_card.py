#!/usr/bin/env python3
"""Fetch Valorant MMR and regenerate valorant_card.svg."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

NAME = "GunmaN"
TAG = "1803"
REGION = "ap"
API = f"https://api.kyroskoh.xyz/valorant/v1/mmr/{REGION}/{NAME}/{TAG}"
OUT = Path(__file__).resolve().parents[1] / "valorant_card.svg"


def fetch_mmr() -> tuple[str, str]:
    req = urllib.request.Request(
        API,
        headers={
            "User-Agent": "r1tv1kx-profile-readme/1.0",
            "Accept": "text/plain",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8").strip()
    # Expected: "Gold 1 - 79RR"
    m = re.match(r"^(.+?)\s*-\s*(\d+)\s*RR$", text, re.I)
    if not m:
        raise SystemExit(f"Unexpected MMR payload: {text!r}")
    return m.group(1).strip(), m.group(2).strip()


def render(rank: str, rr: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="160" viewBox="0 0 420 160" role="img" aria-label="Valorant stats for {NAME}#{TAG}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#6A5ACD"/>
      <stop offset="100%" stop-color="#8B7FD9"/>
    </linearGradient>
  </defs>

  <rect width="420" height="160" rx="12" fill="url(#bg)" stroke="#30363d" stroke-width="1"/>
  <rect x="0" y="0" width="6" height="160" fill="url(#accent)"/>

  <text x="28" y="36" fill="#8B949E" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12">VALORANT · {REGION.upper()}</text>
  <text x="28" y="64" fill="#E6EDF3" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="22" font-weight="700">{NAME}#{TAG}</text>

  <text x="28" y="104" fill="#6A5ACD" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="28" font-weight="700">{rank}</text>
  <text x="28" y="132" fill="#C9D1D9" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">{rr} RR · competitive</text>

  <text x="300" y="132" fill="#484F58" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11">auto-updated</text>
</svg>
'''


def main() -> None:
    rank, rr = fetch_mmr()
    OUT.write_text(render(rank, rr), encoding="utf-8")
    print(f"Wrote {OUT} -> {rank} / {rr} RR")


if __name__ == "__main__":
    main()
