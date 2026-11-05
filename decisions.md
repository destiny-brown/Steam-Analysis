# Decisions log

One entry per work session. Newest at the top. The next session (human or AI)
reads this file first, then README.md. The report's method section is a
cleaned version of this log, not a reconstructed story.

## 2026-11-05 (evening) — Destiny (with AI pair)

**Decisions (recorded before the run):**

1. Reviews refused. The proposal's original historical attention series was
   Steam review velocity (`appreviews` weekly count and positive ratio).
   Probe on 2026-11-05 ~17:49 HKT:
   `GET https://store.steampowered.com/appreviews/730?json=1&filter=summary`
   returns `HTTP/1.1 302 Moved Temporarily, Location:
   https://store.steampowered.com/` from nginx, with every client tried
   (urllib, curl, browser UA, mature-content cookies). The
   `api.steampowered.com` variant returns 404. SteamSpy exposes only current
   cumulative totals, no weekly history. Verdict: weekly review history is
   not collectible. Reviews join Twitch on the refused list (README updated).
2. Add `major_update` and `days_since_major_update` columns, derived from the
   news JSON we already hold. Heuristic: a post is major if its lowercase
   title matches `\b(update|patch)\s*\d` or contains any of: expansion, dlc,
   season, chapter, new hero, new map, new region, new agent, new operator,
   free-to-play. Rationale: weekly spikes are event-driven (lag-1
   autocorrelation of log-growth is 0.046), and `news_count` treats a hotfix
   and an expansion launch as equal. Zero new data collection, zero new
   leakage surface.
3. Add a `growth_4w_missing` indicator in train.py. Blank `growth_4w` (first
   four weeks of every game, 96 of 240 usable rows) was being fed to models
   as the literal value 0.0, which claims "no growth" where the truth is
   "no trailing window exists".
4. Log-transform `peak` and `mean_players` inside train.py's feature matrix
   (raw columns stay in the panel for the baseline and the stats table).
   Raw counts span 171x across games (7.7k to 1.3M); the target is a log
   ratio, so features should be scale-free.
5. One rebuild, one retrain, whatever the numbers say. Validation is not
   being used to iterate.

**Results (appended after the run):**

Validation MAE, one rebuild + one retrain, commits pending:

| Model | Val MAE (before) | Val MAE (after) |
| --- | --- | --- |
| unchanged peak | 0.0895 | 0.0895 |
| weekday pattern | 0.2255 | 0.2255 |
| ridge | 0.1054 | 0.0955 |
| XGBoost | 0.1312 | 0.1099 |

Ablation (XGBoost, validation): full 0.1099 / no_calendar 0.1141 /
no_peer 0.1099 / no_major_update 0.1123.

Reading: every change helped. Ridge closed most of the gap to the baseline;
XGBoost's gap halved (0.042 to 0.020). The ablation now shows calendar and
major_update each contributing (removing either makes validation worse),
reversing last session's sign on the calendar. The baseline still leads;
that remains the honest headline unless the test weeks say otherwise.
`major_update` flagged 53/312 panel rows, concentrated in live-service
games (PUBG, Apex), which is the expected shape. peers.csv still missing,
so no_peer still equals full.

## 2026-11-05 — Destiny (with AI pair)

**Validation MAE (log-growth), after rebuilding the panel with `analysis/calendar.csv` (commit 90e48c7):**

| Model | Val MAE |
| --- | --- |
| unchanged peak | 0.0895 |
| weekday pattern | 0.2255 |
| ridge | 0.1054 |
| XGBoost (shallow, depth 3) | 0.1312 |

Ablation (XGBoost, validation): full 0.1312 / no_calendar 0.1267 / no_peer 0.1312.
Surge base rate on train+val: 8/240 = 3.3%.

**Decisions and observations:**

- Panel window fixed: weeks starting 2026-08-10 through 2026-11-02 only
  (312 rows = 24 games x 13 weeks). Old monthly rows (2012+) excluded;
  `resolution_for` now labels single-sample weeks "monthly" instead of
  "hourly" (commit 69ed9ec).
- Calendar flags verified by hand against `analysis/calendar.csv` for all
  13 weeks of appid 730. All correct, including the live row (2026-11-02)
  showing `sale_next_week = 0` for the 9-15 Nov forecast week.
- Calendar features are real signal but XGBoost overfits them at 192
  training rows / 13 features: no_calendar beats full on validation.
  We keep the locked ladder as-is; we do not tune on validation.
- `peer_median_growth` is still empty: waiting on `analysis/peers.csv`
  (Soha). The no_peer ablation row is identical to full until then.
- Historical test weeks (19 Oct - 1 Nov) remain untouched. The test
  scoring block in `model/train.py` stays commented out until Saturday.
- Chronos-2 attempt scheduled Saturday 7 Nov; if install fails, the
  verbatim error goes to `model/results/chronos_note.txt`.
- `Lecture Notes/` removed from git tracking and added to .gitignore.

**Next session starts here:** rebuild + retrain once `analysis/peers.csv`
exists, then freeze features for Saturday's full run (test once, ablation
on test, Chronos attempt).
