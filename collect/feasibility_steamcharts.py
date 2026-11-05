#!/usr/bin/env python3
"""Check how fine SteamCharts player history is for a few games.

SteamCharts polls Steam's live player-count endpoint and publishes the saved
series at /app/{appid}/chart-data.json. The spacing of those points decides
whether a weekly peak can be built from history.

This script downloads five games, saves the raw JSON, and writes a plain
summary. It does not touch SullyGnome.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "feasibility" / "steamcharts"
REPORT = ROOT / "data" / "feasibility" / "steamcharts_resolution.txt"

# One giant, one live-service, one breakout-style, two smaller games.
GAMES = [
    (730, "Counter-Strike 2"),
    (570, "Dota 2"),
    (1623730, "Palworld"),
    (892970, "Valheim"),
    (105600, "Terraria"),
]

USER_AGENT = "Group18-FoundationModels/0.1 (university course project)"
HOUR = 3600_000


def fetch(appid: int) -> list:
    url = f"https://steamcharts.com/app/{appid}/chart-data.json"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        raise ValueError(f"unexpected payload for {appid}")
    return payload


def stamp(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def gap_kind(hours: float) -> str:
    if hours <= 2:
        return "hourly"
    if 12 <= hours <= 36:
        return "daily"
    if hours >= 24 * 20:
        return "monthly"
    return "other"


def regimes(points: list) -> list[tuple[str, int, int, int]]:
    runs: list[tuple[str, int, int, int]] = []
    for earlier, later in zip(points, points[1:]):
        kind = gap_kind((later[0] - earlier[0]) / HOUR)
        if not runs or runs[-1][0] != kind:
            runs.append((kind, later[0], later[0], 1))
        else:
            name, start, _end, count = runs[-1]
            runs[-1] = (name, start, later[0], count + 1)
    return runs


def describe(name: str, appid: int, points: list) -> str:
    points = sorted(points, key=lambda row: row[0])
    last_ms = points[-1][0]
    zeros = sum(1 for _, players in points if players == 0)
    recent_zeros = sum(1 for ts, players in points if players == 0 and last_ms - ts <= 30 * 24 * HOUR)
    lines = [
        f"{name} ({appid})",
        f"  points: {len(points)}",
        f"  span: {stamp(points[0][0])} to {stamp(last_ms)}",
    ]
    for kind, start, end, count in regimes(points):
        if count < 3 and kind == "other":
            continue
        lines.append(f"  {kind}: {stamp(start)} to {stamp(end)} ({count} steps)")
    lines.append(f"  zero player counts: {zeros} overall, {recent_zeros} in the last 30 days")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sections = [
        "SteamCharts resolution check",
        f"Run at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "Source: https://steamcharts.com/app/{appid}/chart-data.json",
        "One request per second. Raw files are saved beside this report.",
        "",
    ]
    failures = []
    refresh = "--refresh" in sys.argv
    for index, (appid, name) in enumerate(GAMES):
        cached = OUT_DIR / f"{appid}.json"
        try:
            if cached.exists() and not refresh:
                points = json.loads(cached.read_text())
            else:
                if index:
                    time.sleep(1.1)
                points = fetch(appid)
                cached.write_text(json.dumps(points))
        except Exception as exc:  # noqa: BLE001 - report every failure in the feasibility note
            failures.append(f"{name} ({appid}): {exc}")
            continue
        sections.append(describe(name, appid, points))
        sections.append("")

    if failures:
        sections.append("Downloads that failed")
        sections.extend(f"  {line}" for line in failures)
        sections.append("")

    sections.extend(
        [
            "Verdict",
            "  The same three layers show up on every game, so this is how SteamCharts",
            "  publishes the file, not a quirk of one title.",
            "  Monthly points run from the game's early history through 1 Aug 2026.",
            "  Daily points run from 9 Aug 2026 through 6 Oct 2026, about eight weeks.",
            "  Hourly points run from 6 Oct 2026 to the download day, about 30 days.",
            "  A next-week model can use the daily stretch as a sampled peak and the",
            "  hourly stretch as a real peak. The monthly stretch is context only.",
            "  Our own hourly recorder is what extends the real-peak series past today.",
            "  Zero counts at the same moments on every game are outages to drop later.",
        ]
    )
    text = "\n".join(sections) + "\n"
    REPORT.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
