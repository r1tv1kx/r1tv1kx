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


def render(rank: str, rr: int, peak_rank: str, peak_act: str, s: dict) -> str:
    hours = fmt_int(int(s["hours"]))
    matches = fmt_int(int(s["matches"]))
    level = int(s["level"])
    kd = s["kd"]
    acs = s["acs"]
    win = s["win_pct"]
    hs = s["hs"]
    agent = s.get("top_agent", "—")
    kills = fmt_int(int(s["kills"]))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="210" viewBox="0 0 640 210" role="img" aria-label="Valorant stats for {NAME}#{TAG}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0C1014"/>
      <stop offset="100%" stop-color="#12181F"/>
    </linearGradient>
  </defs>

  <rect width="640" height="210" rx="12" fill="url(#bg)"/>
  <rect x="0.6" y="0.6" width="638.8" height="208.8" rx="12" fill="none" stroke="#1E262E" stroke-width="1"/>
  <circle cx="24" cy="28" r="3" fill="#FF4655"/>

  <text x="38" y="32" fill="#8A939C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="12" letter-spacing="0.4">valorant · competitive</text>
  <text x="616" y="32" text-anchor="end" fill="#D8DEE5" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="13" font-weight="600">{NAME}#{TAG}</text>

  <text x="28" y="84" fill="#F4F0EA" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="-0.6">{rank}</text>
  <text x="210" y="84" fill="#FF4655" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="-0.6">{rr}</text>
  <text x="290" y="84" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="13">rr</text>

  <text x="616" y="68" text-anchor="end" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">peak</text>
  <text x="616" y="90" text-anchor="end" fill="#D8DEE5" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600">{peak_rank}</text>
  <text x="616" y="108" text-anchor="end" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">{peak_act}</text>

  <line x1="28" y1="122" x2="612" y2="122" stroke="#1C242C" stroke-width="1"/>

  <text x="28" y="152" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">k/d</text>
  <text x="28" y="176" fill="#F4F0EA" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="22" font-weight="600">{kd}</text>

  <text x="120" y="152" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">acs</text>
  <text x="120" y="176" fill="#F4F0EA" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="22" font-weight="600">{acs}</text>

  <text x="220" y="152" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">win%</text>
  <text x="220" y="176" fill="#F4F0EA" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="22" font-weight="600">{win}</text>

  <text x="320" y="152" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">hs%</text>
  <text x="320" y="176" fill="#F4F0EA" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="22" font-weight="600">{hs}</text>

  <text x="420" y="152" fill="#6A737C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">kills</text>
  <text x="420" y="176" fill="#F4F0EA" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="22" font-weight="600">{kills}</text>

  <text x="28" y="198" fill="#5A636C" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" font-size="11">lvl {level}  ·  {hours}h  ·  {matches} matches  ·  main {agent.lower()}</text>
</svg>
'''


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
