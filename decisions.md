# Decisions log

One entry per work session. Newest at the top. The next session (human or AI)
reads this file first, then README.md. The report's method section is a
cleaned version of this log, not a reconstructed story.

## 2026-11-08 (Sunday, seal night) — Destiny (with AI pair)

**The live forecast is sealed.** `data/live/forecast_2026-11-09.csv` was
emitted at 2026-11-08T15:59:30Z (23:59 HKT Sunday), committed and pushed the
same night — before Monday 00:00 UTC and before any of the 9-15 Nov week
existed. The file is never edited again; scoring happens Mon 16 Nov against
the recorder data.

**Fit decision (the open question from Saturday):** ridge (alpha=1.0, the
frozen configuration) was refit on all 288 labeled rows — train + validation
+ historical test, weeks of 10 Aug - 1 Nov. Rationale: standard
post-evaluation practice; the test weeks precede the forecast week
chronologically, so no leakage. The alternative (train-only 192-row fit, the
exact object that scored 0.876) was rejected because withholding 96 labeled
weeks from the final fit wastes information for a one-shot forecast. The
checkpoint PDF submitted tonight states this choice publicly.

**Forecast content:** all 24 games predicted negative log-growth, range
-0.032 (Lost Ark) to -0.179 (Valheim). Consistent with the post-Halloween
cooldown signal (22/24 negative wow_growth in the live feature week). Apex
Legends (+0.236 wow with major update) is still predicted down (-0.125);
Path of Exile's 13 Nov expansion is invisible to the features (news features
describe the live week, not the forecast week) — the known wildcard, noted in
advance, scored as the model stands.

**Infrastructure:** SteamCharts re-downloaded tonight (`--refresh`, 24/24
saved) so the live feature row includes the full weekend; panel rebuilt
(312 rows). Mac recorder healthy (last run 23:09 HKT). Cloud recorder leg
last wrote 2026-11-07T12:17Z — stale ~36h at seal time; investigate at the
16 Nov merge, Mac leg is the scoring leg.

`model/forecast.py` imports FEATURES/load_panel/ridge_fit/ridge_predict from
`train.py` verbatim so feature logic cannot drift; it refuses to run at or
after Monday 00:00 UTC and validates 288 labeled / 24 live rows and the
games.csv game set before writing.

## 2026-11-07 (Saturday, freeze day) — Destiny (with AI pair)

**The historical test weeks were scored once, today, 20:55 HKT.** Models are
the frozen train-fit ones from 6 Nov; no refit on train+val, no second pass.

**Test MAE of log-growth (48 rows, weeks of 19 Oct and 26 Oct):**

| Model | Test MAE | Ratio to baseline |
| --- | --- | --- |
| unchanged peak | 0.1440 | 1.000 |
| weekday pattern | 0.3300 | 2.291 |
| ridge | 0.1263 | 0.876 |
| XGBoost | 0.1319 | 0.916 |

Test ablation (XGBoost): full 0.1319 / no_calendar 0.1413 / no_peer 0.1424 /
no_major_update 0.1334. Every feature family contributes on test: removing
any of them makes the score worse.

**Headline: ridge and XGBoost both beat the unchanged-peak baseline on the
held-out test weeks (ratios 0.876 and 0.916).** The test weeks were harder
than validation (baseline 0.1440 vs 0.0895 — Next Fest and Scream weeks are
volatile), and the models' edge grew exactly there.

**For the report:**
- XGBoost train MAE 0.0442 vs test 0.1319 is the overfitting signature;
  ridge (train 0.1117, test 0.1263) generalizes far better. This is the
  L5 bias-variance exhibit, with numbers.
- The validation ablation flipped signs between runs (noise on 48 rows);
  the test ablation is unanimous. That contrast is itself a finding:
  small validation samples cannot adjudicate feature families.
- Weekday pattern is discredited on both splits; it stays in the ladder as
  the negative control.

**Decisions made today:** test ablation replaces the validation ablation in
model/results/ablation.csv (validation numbers preserved in the 5-6 Nov
entries above). validation.csv now carries train_mae as the README requires.
Remaining today: Chronos-2 attempt, then freeze. Tomorrow: seal the live
forecast by 23:00 HKT.

**Chronos-2 small, zero-shot — ran successfully (21:00 HKT).** Test MAE
0.1401, ratio 0.973: it beats the baseline with zero training on our data,
but loses to ridge (0.876) and XGBoost (0.916). Full per-row detail in
model/results/chronos_note.txt. Final ladder on the historical test weeks:

| Model | Test MAE | Ratio |
| --- | --- | --- |
| unchanged peak | 0.1440 | 1.000 |
| weekday pattern | 0.3300 | 2.291 |
| ridge | 0.1263 | 0.876 |
| XGBoost | 0.1319 | 0.916 |
| Chronos-2 small (zero-shot) | 0.1401 | 0.973 |

For the talk: the foundation model with no training on our data nearly
matches a tuned baseline, but a ridge on engineered features wins — the
expected result when the target series is short and the features are
event-informed. (Process note: the first attempt failed with
`ImportError: cannot import name 'Chronos2Pipeline' from 'chronos'
(model/chronos.py)` — the script's own filename shadowed the package.
Renamed to model/run_chronos.py. The failed verbatim error was
overwritten by the successful note.)

**Forecast model for tomorrow's sealed file: ridge** — the best test
ratio (0.876). The model is frozen; only the live-week features change.

**FREEZE.** No further model changes before the 16 Nov scoring.

## 2026-11-06 (late) — Destiny (with AI pair)

**Cloud redundancy for the recorder (commit 81e2b1e).** The MacBook cannot
stay awake for the full scored week (commutes, lid closures), so a GitHub
Actions workflow now runs `collect/collect_once.py` hourly at :05 UTC.
Design decision: the cloud collector writes `data/live/cloud/`, NOT the
Mac's files, so bot pushes and local pushes can never collide on the same
CSV. `collect_once.py` gained an `--out-dir` flag; the Mac launchd job is
unchanged. First manual dispatch succeeded at 13:20 UTC (24/24, 7.9s,
commit 89d2c4d). Cron caveats: Actions schedules can lag minutes to an
hour under load. Scoring on 16 Nov will merge both series, dedupe by
(appid, hour) preferring the Mac copy, and use the SteamCharts hourly
re-download as a third leg. The two sources also cross-check each other:
same hour, same public number, independent collectors.

**For the report's data-access section:** the collection infrastructure
itself became part of the reliability story — a laptop recorder with known
gaps, a cloud replica, and a third-party archive (SteamCharts) as backup,
with honesty about which hours are missing recorded in n_samples.

## 2026-11-06 — Destiny (with AI pair)

**Trigger:** Soha's `analysis/peers.csv` arrived (commit 1db74c5). Validated
before the run: 24/24 appids, five groups (shooter 6, coop_live_service 5,
survival_sandbox 5, rpg 4, pvp_other 4), all >= the README minimum of 3.
One rebuild, one retrain.

**Validation MAE, with peers (previous run in brackets):**

| Model | Val MAE |
| --- | --- |
| unchanged peak | 0.0895 (0.0895) |
| weekday pattern | 0.2255 (0.2255) |
| ridge | 0.0980 (0.0955) |
| XGBoost | 0.1091 (0.1099) |

Ablation (XGBoost, validation): full 0.1091 / no_calendar 0.1080 /
no_peer 0.1099 / no_major_update 0.1144.

**Sanity checks on the peer column:** populated 240/240 usable rows;
peer_set_size 3-5 as designed. Sign agreement between a game's log-growth
and its peer median: 119/240 = 49.6% — a coin flip, consistent with the
lag-1 autocorrelation of 0.046. Weekly growth is near-noise, so peer
momentum cannot align either. Soha's report section should state this
directly.

**Reading:** peers changed little (XGBoost +0.0008 better, ridge -0.0025
worse — both inside validation noise on 48 rows). `major_update` remains
the clearest feature contribution (removing it: 0.1091 -> 0.1144).
Calendar flipped sign again between runs (helped yesterday, hurts today),
which confirms these small ablation differences are within noise; the
test-week run is what adjudicates. The ladder is now FINAL for Saturday:
all designed inputs exist. No further feature changes before the freeze.

**Tomorrow (Saturday 7 Nov), in order:** full ladder -> score the two
historical test weeks ONCE into model/results/test.csv with ratios ->
ablation on test -> Chronos-2 small zero-shot (verbatim error to
chronos_note.txt if install fails). Then freeze.

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

**Why each model moved (for the method section):** Ridge gained mostly from
the log-transform: ridge is linear, raw peaks span 171x across games, and
logging converts multiplicative scale differences into the additive
language the log-growth target speaks. XGBoost gained mostly from the
`growth_4w_missing` indicator (96 of 240 usable rows previously carried a
fabricated literal 0.0 that trees were splitting on) and from
`major_update`, its first genuine event feature. Tree splits are invariant
to monotonic transforms, so the log-transform alone would not have moved
XGBoost. The calendar ablation sign-flip (removing calendar features hurt
before the fix, helps after) is the signature of a model that was too
overfit to hear real signal over the garbage. Baseline and weekday-pattern
scores are unchanged, as expected: neither reads the feature matrix, so
their stability confirms the edits did not leak into the target pipeline.

**For the report's data-access section:** This is the second time the
project hit the same wall in different clothing: Twitch has history we
cannot access; reviews had access that no longer exists. Both refusals
have the same root cause — features that depend on platforms' goodwill
toward unofficial data access, and that goodwill can vanish mid-project.
The data-science pipeline does not start at cleaning; it starts at
discovering which doors are still open. (`appreviews` was never an
official documented endpoint; it was the storefront's internal JSON feed
that the community reused until nginx began issuing an unconditional 302.
The documented ISteamNews and player-count APIs worked throughout.)

**For the talk:** the error metric sentence, to preempt confusion: "Our
error metric is MAE of log-growth, where lower is better; we compare each
model against the unchanged-peak baseline's error, so a ratio below 1
means the model added value." In plain terms, exp(MAE) is the typical
multiplier error: baseline 0.0895 is about +/-9.4%, ridge 0.0955 about
+/-10%, XGBoost 0.1099 about +/-11.6%.

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
