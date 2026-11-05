# Decisions log

One entry per work session. Newest at the top. The next session (human or AI)
reads this file first, then README.md. The report's method section is a
cleaned version of this log, not a reconstructed story.

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
