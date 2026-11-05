#!/usr/bin/env python3
"""Build data/processed/week_panel.csv from raw SteamCharts, news, calendar, and peers.

One row per game per week. A feature for week t uses only timestamps inside week t or earlier.
Columns follow README.md. next_peak and log_growth are empty on the live forecast row.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES_CSV = ROOT / "collect" / "games.csv"
STEAMCHARTS_DIR = ROOT / "data" / "feasibility" / "steamcharts"
NEWS_DIR = ROOT / "data" / "news"
CALENDAR_CSV = ROOT / "analysis" / "calendar.csv"
PEERS_CSV = ROOT / "analysis" / "peers.csv"
OUT_CSV = ROOT / "data" / "processed" / "week_panel.csv"

HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
WEEK = timedelta(days=7)


def read_games() -> list[dict[str, str]]:
    return list(csv.DictReader(GAMES_CSV.open()))


def parse_steamcharts(path: Path) -> list[tuple[datetime, int]]:
    payload = json.loads(path.read_text())
    points = []
    for ts_ms, players in payload:
        ts = datetime.fromtimestamp(ts_ms / 1000, timezone.utc)
        points.append((ts, int(players)))
    points.sort(key=lambda x: x[0])
    return points


def resolution_for(week_start: datetime, points: list[tuple[datetime, int]]) -> str:
    week_end = week_start + WEEK
    inside = [(ts, p) for ts, p in points if week_start <= ts < week_end]
    if len(inside) < 2:
        return "monthly"
    gaps = []
    for (ts1, _), (ts2, _) in zip(inside, inside[1:]):
        gaps.append(ts2 - ts1)
    med_gap = sorted(gaps)[len(gaps) // 2]
    if med_gap <= timedelta(hours=2):
        return "hourly"
    if med_gap >= timedelta(days=20):
        return "monthly"
    return "daily"


def week_stats(week_start: datetime, points: list[tuple[datetime, int]]) -> dict:
    week_end = week_start + WEEK
    inside = [(ts, p) for ts, p in points if week_start <= ts < week_end]
    n_samples = len(inside)
    n_zeros = sum(1 for _, p in inside if p == 0)
    cleaned = []
    for idx, (ts, p) in enumerate(inside):
        if p != 0:
            cleaned.append(p)
            continue
        prev_p = inside[idx - 1][1] if idx > 0 else None
        next_p = inside[idx + 1][1] if idx + 1 < len(inside) else None
        if (prev_p is not None and prev_p > 0) and (next_p is not None and next_p > 0):
            continue
        cleaned.append(p)
    if not cleaned:
        peak = 0
        mean_players = 0.0
    else:
        peak = max(cleaned)
        mean_players = sum(cleaned) / len(cleaned)
    return {
        "n_samples": n_samples,
        "n_zeros": n_zeros,
        "peak": peak,
        "mean_players": round(mean_players, 2),
    }


def mad(values: list[float], center: float) -> float:
    deviations = sorted(abs(v - center) for v in values)
    n = len(deviations)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return deviations[mid]
    return (deviations[mid - 1] + deviations[mid]) / 2


def median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def load_news_counts() -> dict[str, list[datetime]]:
    counts = {}
    if not NEWS_DIR.exists():
        return counts
    for path in NEWS_DIR.glob("*.json"):
        appid = path.stem
        payload = json.loads(path.read_text())
        items = payload.get("appnews", {}).get("newsitems", [])
        stamps = []
        for item in items:
            ts = item.get("date") or item.get("posttime")
            if ts:
                stamps.append(datetime.fromtimestamp(int(ts), timezone.utc))
        stamps.sort()
        counts[appid] = stamps
    return counts


def load_calendar() -> list[dict[str, str]]:
    if not CALENDAR_CSV.exists():
        return []
    return list(csv.DictReader(CALENDAR_CSV.open()))


def load_peers() -> dict[str, str]:
    if not PEERS_CSV.exists():
        return {}
    return {row["appid"].strip(): row["peer_group"].strip() for row in csv.DictReader(PEERS_CSV.open())}


def main() -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    games = read_games()
    news_counts = load_news_counts()
    calendar = load_calendar()
    peers = load_peers()

    panel_by_game: dict[str, list[dict]] = {}

    for game in games:
        appid = game["appid"].strip()
        name = game["name"].strip()
        path = STEAMCHARTS_DIR / f"{appid}.json"
        if not path.exists():
            print(f"WARNING missing {path.name} for {name}")
            continue
        points = parse_steamcharts(path)
        if not points:
            continue
        first_ts = points[0][0]
        last_ts = points[-1][0]
        monday = first_ts - timedelta(days=first_ts.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        rows = []
        week_start = monday
        while week_start <= last_ts:
            week_end = week_start + WEEK
            stats = week_stats(week_start, points)
            if stats["peak"] > 0:
                resolution = resolution_for(week_start, points)
                if week_start >= datetime(2026, 8, 10, tzinfo=timezone.utc) or resolution == "hourly":
                    rows.append(
                        {
                            "appid": appid,
                            "name": name,
                            "week_start": week_start.strftime("%Y-%m-%d"),
                            "resolution": resolution,
                            "n_samples": stats["n_samples"],
                            "n_zeros": stats["n_zeros"],
                            "peak": stats["peak"],
                            "mean_players": stats["mean_players"],
                        }
                    )
            week_start += WEEK
        panel_by_game[appid] = rows

    wow_growth: dict[str, dict[str, float]] = defaultdict(dict)
    for appid, rows in panel_by_game.items():
        for idx, row in enumerate(rows):
            prev = rows[idx - 1] if idx > 0 else None
            if prev and prev["peak"] > 0 and row["peak"] > 0:
                wow_growth[appid][row["week_start"]] = math.log(row["peak"] / prev["peak"])
            else:
                wow_growth[appid][row["week_start"]] = 0.0

    out_rows = []
    for appid, rows in panel_by_game.items():
        peer_group = peers.get(appid, "")
        for idx, row in enumerate(rows):
            week_start_str = row["week_start"]
            week_start = datetime.strptime(week_start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            week_end = week_start + WEEK
            sunday = week_end - timedelta(seconds=1)

            next_row = rows[idx + 1] if idx + 1 < len(rows) else None
            next_peak = next_row["peak"] if next_row else ""
            log_growth = (
                round(math.log(next_row["peak"] / row["peak"]), 6) if next_row and row["peak"] > 0 else ""
            )

            row_4w = rows[idx - 4] if idx >= 4 else None
            growth_4w = (
                round(math.log(row["peak"] / row_4w["peak"]), 6)
                if row_4w and row_4w["peak"] > 0 and row["peak"] > 0
                else ""
            )

            trailing = [r["peak"] for r in rows[max(0, idx - 4) : idx] if r["peak"] > 0]
            median_4w = round(median(trailing), 2) if trailing else ""
            mad_4w = round(mad(trailing, median(trailing)), 2) if trailing else ""

            sale_this_week = 0
            sale_next_week = 0
            holiday_count = 0
            for cal in calendar:
                date_str = cal.get("date", "")
                announced = cal.get("announced_on", "")
                if not date_str:
                    continue
                cal_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                announced_date = (
                    datetime.strptime(announced, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if announced
                    else cal_date
                )
                if cal.get("sale_name", "").strip():
                    if week_start <= cal_date < week_end and announced_date <= sunday:
                        sale_this_week = 1
                    if week_end <= cal_date < week_end + WEEK and announced_date <= sunday:
                        sale_next_week = 1
                if cal.get("holiday_name", "").strip():
                    if week_start <= cal_date < week_end:
                        holiday_count += 1

            peer_values = []
            peer_set_size = 0
            if peer_group:
                for other_appid, other_rows in panel_by_game.items():
                    if other_appid == appid:
                        continue
                    other_group = peers.get(other_appid, "")
                    if other_group != peer_group:
                        continue
                    if week_start_str in wow_growth[other_appid]:
                        peer_values.append(wow_growth[other_appid][week_start_str])
                peer_set_size = len(peer_values)
            peer_median_growth = round(median(peer_values), 6) if peer_values else ""

            news_count = 0
            days_since_news = ""
            stamps = news_counts.get(appid, [])
            for ts in stamps:
                if week_start <= ts < week_end:
                    news_count += 1
            past_stamps = [ts for ts in stamps if ts <= sunday]
            if past_stamps:
                days_since_news = (sunday - past_stamps[-1]).days

            out_rows.append(
                {
                    "appid": appid,
                    "name": row["name"],
                    "week_start": week_start_str,
                    "resolution": row["resolution"],
                    "n_samples": row["n_samples"],
                    "n_zeros": row["n_zeros"],
                    "peak": row["peak"],
                    "mean_players": row["mean_players"],
                    "next_peak": next_peak,
                    "log_growth": log_growth,
                    "wow_growth": round(wow_growth[appid].get(week_start_str, 0.0), 6),
                    "growth_4w": growth_4w,
                    "median_4w": median_4w,
                    "mad_4w": mad_4w,
                    "weekend_days": 2,
                    "sale_this_week": sale_this_week,
                    "sale_next_week": sale_next_week,
                    "holiday_count": holiday_count,
                    "peer_median_growth": peer_median_growth,
                    "peer_set_size": peer_set_size,
                    "news_count": news_count,
                    "days_since_news": days_since_news,
                }
            )

    fieldnames = [
        "appid",
        "name",
        "week_start",
        "resolution",
        "n_samples",
        "n_zeros",
        "peak",
        "mean_players",
        "next_peak",
        "log_growth",
        "wow_growth",
        "growth_4w",
        "median_4w",
        "mad_4w",
        "weekend_days",
        "sale_this_week",
        "sale_next_week",
        "holiday_count",
        "peer_median_growth",
        "peer_set_size",
        "news_count",
        "days_since_news",
    ]
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"wrote {OUT_CSV} with {len(out_rows)} rows")


if __name__ == "__main__":
    main()
