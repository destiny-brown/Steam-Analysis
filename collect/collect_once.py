#!/usr/bin/env python3
"""Append one live snapshot for every game in collect/games.csv.

Steam player counts are collected on every run. Twitch viewer totals are
collected only when TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET are present
in the environment or in the project .env file.

The Mac must be awake. Hours while it is asleep are gaps, and they are
left as gaps.
"""

from __future__ import annotations

import csv
import fcntl
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "collect" / "games.csv"
LIVE = ROOT / "data" / "live"
LOCK = LIVE / ".collect.lock"
STEAM_CSV = LIVE / "steam_players.csv"
TWITCH_CSV = LIVE / "twitch_streams.csv"
RUNS_CSV = LIVE / "collector_runs.csv"
GAME_IDS = LIVE / "twitch_game_ids.csv"

USER_AGENT = "Group18-FoundationModels/0.1 (university course project)"
TWITCH_PAGES = 3  # 300 streams. Viewer mass sits in the top channels.


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_env() -> dict[str, str]:
    found = dict(os.environ)
    path = ROOT / ".env"
    if not path.exists():
        return found
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        found.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return found


def read_games() -> list[dict[str, str]]:
    with GAMES.open(newline="") as handle:
        return list(csv.DictReader(handle))


def append_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def post_form(url: str, form: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(form).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def collect_steam(games: list[dict[str, str]], collected_at: str) -> tuple[list[dict], int, int]:
    rows = []
    ok = fail = 0
    for index, game in enumerate(games):
        if index:
            time.sleep(0.25)
        appid = game["appid"]
        url = (
            "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
            f"?appid={appid}"
        )
        row = {
            "collected_at_utc": collected_at,
            "appid": appid,
            "name": game["name"],
            "player_count": "",
            "ok": "0",
            "error": "",
        }
        try:
            payload = get_json(url)
            response = payload.get("response", {})
            if response.get("result") != 1 or "player_count" not in response:
                raise ValueError(f"unexpected response: {payload}")
            row["player_count"] = response["player_count"]
            row["ok"] = "1"
            ok += 1
        except Exception as exc:  # noqa: BLE001 - one bad appid must not stop the hour
            row["error"] = str(exc).replace("\n", " ")[:300]
            fail += 1
        rows.append(row)
    return rows, ok, fail


def twitch_token(env: dict[str, str]) -> str:
    payload = post_form(
        "https://id.twitch.tv/oauth2/token",
        {
            "client_id": env["TWITCH_CLIENT_ID"],
            "client_secret": env["TWITCH_CLIENT_SECRET"],
            "grant_type": "client_credentials",
        },
    )
    return payload["access_token"]


def load_game_ids() -> dict[str, str]:
    if not GAME_IDS.exists():
        return {}
    with GAME_IDS.open(newline="") as handle:
        return {row["twitch_name"]: row["twitch_game_id"] for row in csv.DictReader(handle)}


def save_game_ids(mapping: dict[str, str]) -> None:
    rows = [{"twitch_name": name, "twitch_game_id": game_id} for name, game_id in sorted(mapping.items())]
    GAME_IDS.parent.mkdir(parents=True, exist_ok=True)
    with GAME_IDS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["twitch_name", "twitch_game_id"])
        writer.writeheader()
        writer.writerows(rows)


def resolve_game_ids(games: list[dict[str, str]], headers: dict[str, str]) -> dict[str, str]:
    mapping = load_game_ids()
    missing = []
    for game in games:
        name = game["twitch_name"].strip()
        if name and name not in mapping:
            missing.append(name)
    for start in range(0, len(missing), 100):
        batch = missing[start : start + 100]
        query = "&".join("name=" + urllib.parse.quote(name) for name in batch)
        payload = get_json(f"https://api.twitch.tv/helix/games?{query}", headers)
        for item in payload.get("data", []):
            mapping[item["name"]] = item["id"]
    save_game_ids(mapping)
    return mapping


def collect_twitch(games: list[dict[str, str]], collected_at: str, env: dict[str, str]) -> tuple[list[dict], int, int, str]:
    client_id = env.get("TWITCH_CLIENT_ID", "").strip()
    client_secret = env.get("TWITCH_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return [], 0, 0, "skipped_no_credentials"

    token = twitch_token(env)
    headers = {"Client-Id": client_id, "Authorization": f"Bearer {token}"}
    game_ids = resolve_game_ids(games, headers)
    rows = []
    ok = fail = 0
    for game in games:
        twitch_name = game["twitch_name"].strip()
        game_id = game_ids.get(twitch_name, "")
        row = {
            "collected_at_utc": collected_at,
            "appid": game["appid"],
            "name": game["name"],
            "twitch_name": twitch_name,
            "twitch_game_id": game_id,
            "viewer_sum": "",
            "stream_count": "",
            "top_viewers": "",
            "pages": "",
            "truncated": "",
            "ok": "0",
            "error": "",
        }
        if not game_id:
            row["error"] = "twitch category name not found"
            fail += 1
            rows.append(row)
            continue
        try:
            viewers, pages, truncated = sample_streams(game_id, headers)
            row.update(
                {
                    "viewer_sum": sum(viewers),
                    "stream_count": len(viewers),
                    "top_viewers": max(viewers) if viewers else 0,
                    "pages": pages,
                    "truncated": "1" if truncated else "0",
                    "ok": "1",
                }
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc).replace("\n", " ")[:300]
            fail += 1
        rows.append(row)
        time.sleep(0.2)
    return rows, ok, fail, "ok"


def sample_streams(game_id: str, headers: dict[str, str]) -> tuple[list[int], int, bool]:
    viewers: list[int] = []
    cursor = ""
    pages = 0
    truncated = False
    while pages < TWITCH_PAGES:
        query = f"game_id={urllib.parse.quote(game_id)}&first=100"
        if cursor:
            query += f"&after={urllib.parse.quote(cursor)}"
        payload = get_json(f"https://api.twitch.tv/helix/streams?{query}", headers)
        batch = payload.get("data", [])
        viewers.extend(int(item.get("viewer_count") or 0) for item in batch)
        pages += 1
        cursor = (payload.get("pagination") or {}).get("cursor", "")
        if len(batch) < 100 or not cursor:
            break
    else:
        truncated = True
    return viewers, pages, truncated


def last_steam_stamp() -> str:
    if not STEAM_CSV.exists():
        return ""
    last = ""
    with STEAM_CSV.open(newline="") as handle:
        for row in csv.DictReader(handle):
            last = row["collected_at_utc"]
    return last


def status() -> None:
    steam_rows = twitch_rows = runs = 0
    if STEAM_CSV.exists():
        with STEAM_CSV.open(newline="") as handle:
            steam_rows = sum(1 for _ in csv.DictReader(handle))
    if TWITCH_CSV.exists():
        with TWITCH_CSV.open(newline="") as handle:
            twitch_rows = sum(1 for _ in csv.DictReader(handle))
    last_run = ""
    if RUNS_CSV.exists():
        with RUNS_CSV.open(newline="") as handle:
            for row in csv.DictReader(handle):
                runs += 1
                last_run = row
    print(f"steam rows: {steam_rows}")
    print(f"twitch rows: {twitch_rows}")
    print(f"runs: {runs}")
    if last_run:
        print(
            "last run: "
            f"{last_run['collected_at_utc']} "
            f"steam {last_run['steam_ok']} ok / {last_run['steam_fail']} fail, "
            f"twitch {last_run['twitch_status']}"
        )
    else:
        print("no runs yet")


def main() -> int:
    LIVE.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("another collection is already running")
            return 0

        started = time.time()
        collected_at = utc_now()
        previous = last_steam_stamp()
        games = read_games()
        steam_rows, steam_ok, steam_fail = collect_steam(games, collected_at)
        append_rows(
            STEAM_CSV,
            ["collected_at_utc", "appid", "name", "player_count", "ok", "error"],
            steam_rows,
        )
        twitch_rows, twitch_ok, twitch_fail, twitch_status = collect_twitch(games, collected_at, load_env())
        if twitch_rows:
            append_rows(
                TWITCH_CSV,
                [
                    "collected_at_utc",
                    "appid",
                    "name",
                    "twitch_name",
                    "twitch_game_id",
                    "viewer_sum",
                    "stream_count",
                    "top_viewers",
                    "pages",
                    "truncated",
                    "ok",
                    "error",
                ],
                twitch_rows,
            )
        append_rows(
            RUNS_CSV,
            ["collected_at_utc", "steam_ok", "steam_fail", "twitch_ok", "twitch_fail", "twitch_status", "seconds"],
            [
                {
                    "collected_at_utc": collected_at,
                    "steam_ok": steam_ok,
                    "steam_fail": steam_fail,
                    "twitch_ok": twitch_ok,
                    "twitch_fail": twitch_fail,
                    "twitch_status": twitch_status,
                    "seconds": f"{time.time() - started:.1f}",
                }
            ],
        )
        print(
            f"{collected_at} steam {steam_ok} ok / {steam_fail} fail, twitch {twitch_status}"
            + (f" ({twitch_ok} ok / {twitch_fail} fail)" if twitch_status == "ok" else "")
        )
        if previous:
            previous_dt = datetime.strptime(previous, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            current_dt = datetime.strptime(collected_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            gap_hours = (current_dt - previous_dt).total_seconds() / 3600
            if gap_hours > 1.5:
                print(f"warning: {gap_hours:.1f} hours since the previous Steam snapshot; those hours are missing")
        return 0 if steam_fail == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        status()
    else:
        sys.exit(main())
