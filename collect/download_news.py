#!/usr/bin/env python3
"""Download Steam news for every game in collect/games.csv.

Saves raw JSON as {appid}.json under data/news/.
One request per second. Existing files are skipped unless --refresh is passed.
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES_CSV = ROOT / "collect" / "games.csv"
OUT_DIR = ROOT / "data" / "news"
USER_AGENT = "Group18-FoundationModels/0.1 (university course project)"


def fetch(appid: str, count: int = 200) -> dict:
    url = (
        "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
        f"?appid={appid}&count={count}&maxlength=1000&format=json"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or "appnews" not in payload:
        raise ValueError(f"unexpected payload for {appid}")
    return payload


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    refresh = "--refresh" in sys.argv
    games = list(csv.DictReader(GAMES_CSV.open()))
    for index, game in enumerate(games):
        appid = game["appid"].strip()
        name = game["name"].strip()
        out_path = OUT_DIR / f"{appid}.json"
        if out_path.exists() and not refresh:
            print(f"skip {appid} {name} (already exists)")
            continue
        if index:
            time.sleep(1.1)
        try:
            payload = fetch(appid)
            out_path.write_text(json.dumps(payload))
            n_items = len(payload["appnews"].get("newsitems", []))
            print(f"saved {appid} {name} ({n_items} news items)")
        except Exception as exc:
            print(f"ERROR {appid} {name}: {exc}")


if __name__ == "__main__":
    main()
