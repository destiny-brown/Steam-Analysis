# Group 18 — Steam player spike forecast

Predict next week's peak Steam player count from information that is already public on Sunday night.

## Live collection

The hourly recorder reads `collect/games.csv` and appends to `data/live/`.

```bash
python3 collect/collect_once.py
python3 collect/collect_once.py --status
```

Steam player counts are collected on every run. Twitch viewer totals are collected only when `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` are set. Copy `.env.example` to `.env` and fill those in. `.env` is not committed.

On this Mac the recorder is scheduled at 5 minutes past every hour with `collect/group18.steamcollector.plist`. The computer has to be awake. Missing hours stay missing.

## History check

`collect/feasibility_steamcharts.py` reads the saved SteamCharts files and writes `data/feasibility/steamcharts_resolution.txt`. Those files are monthly through 1 August 2026, daily from 9 August to 6 October, and hourly from 6 October.
