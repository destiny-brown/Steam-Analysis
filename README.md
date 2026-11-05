# Group 18 — Steam player spike forecast

On Sunday night, using only information already public, can we forecast next week's peak Steam player count better than assuming the peak will not change?

Repository: https://github.com/destiny-brown/Steam-Analysis

Submission is **Tuesday 17 November 2026**. The forecast file for the week of 9–15 November is sealed by **23:00 Hong Kong time on Sunday 8 November**. That file is not edited after it is saved. The week is scored on **Monday 16 November**, after 07:59 Hong Kong time, when the recorded week is complete. Tuesday is for uploading.

## Team

| Person | Owns | Does not own |
| --- | --- | --- |
| Destiny | The model code, the week-table script the model reads, and the hourly recorder on this Mac | The written analysis, the report, the slides |
| Sienna (Tam Hoi Wing) | The analysis: calendar, peer groups, charts, checking the table, and reading what the model scores mean | Fitting models, writing the report prose |
| Soha | The report and the presentation | Code, new metrics, numbers that are not in a saved file |

Each person edits only their own folder, then pulls, commits, and pushes.

| Person | Folder |
| --- | --- |
| Destiny | `model/`, `collect/`, `data/` |
| Sienna | `analysis/` |
| Soha | `report/` |

```bash
git pull
# edit only your folder
git add model/          # or analysis/ or report/
git commit -m "Describe the change in one sentence."
git push
```

If `git push` is rejected, run `git pull` and push again. Do not overwrite someone else's folder to make the push work.

## Setup

```bash
git clone https://github.com/destiny-brown/Steam-Analysis.git
cd Steam-Analysis
python3 -m venv .venv
source .venv/bin/activate
pip install pandas scikit-learn xgboost matplotlib
```

Destiny installs one more package on Saturday, and only if the first four models already have scores: `pip install chronos-forecasting`.

Copy `.env.example` to `.env` only on the machine that runs the recorder. `.env` is not committed.

## Rules already locked

These do not change after Friday 6 November.

- 24 games, listed in `collect/games.csv`. No new games this week.
- A week is Monday 00:00 UTC through Sunday 23:59 UTC.
- The target is `log(next week peak) - log(this week peak)`. The comparison model predicts 0, which means next week's peak equals this week's peak.
- A surge is next week's peak at least 1.5 times this week's peak, and at least two robust deviations above the trailing four-week median. Report how many such weeks exist. If there are only a few, the growth error is the main result and the surges are examples.
- Train on weeks ending through 4 October 2026. Validate on 5–11 October and 12–18 October. The historical test, touched once, is 19–25 October and 26 October–1 November.
- The live forecast uses information through Sunday 8 November and predicts 9–15 November.
- A Steam sale counts only when its announcement date is already public at the Sunday cutoff.
- SullyGnome is a website you read for one example. It is not downloaded or scraped. The owner asks people not to scrape it.
- Do not invent a metric, a player count, or a model score. If a file does not contain the number, the report says the number is not in yet.

SteamCharts history, already measured in `data/feasibility/steamcharts_resolution.txt`, has three layers on every game we checked: monthly through 1 August 2026, daily from 9 August through 6 October, and hourly from 6 October. About twelve weeks can train a weekly model. Monthly history is context, not a training row.

## What to produce

Destiny's model reads one table, `data/processed/week_panel.csv`. One row is one game for one week. Columns:

| Column | Meaning |
| --- | --- |
| `appid`, `name` | Game |
| `week_start` | Monday of the feature week, `YYYY-MM-DD` |
| `resolution` | `daily` or `hourly`, from the SteamCharts spacing that week |
| `n_samples`, `n_zeros` | How many player observations, and how many were zero |
| `peak` | Maximum player sample in the week |
| `mean_players` | Mean of the samples in the week |
| `next_peak` | Peak of the following week. Empty on the live forecast row |
| `log_growth` | `log(next_peak) - log(peak)`. Empty on the live forecast row |
| `wow_growth` | Log growth versus the previous week, known at Sunday |
| `growth_4w` | Log change versus four weeks earlier |
| `median_4w`, `mad_4w` | Trailing four-week median and median absolute deviation of `peak` |
| `weekend_days` | How many of Mon–Sun are Saturday or Sunday. This is 2 |
| `sale_this_week` | 1 if a major Steam sale is already announced and falls in this week |
| `sale_next_week` | 1 only if the next week's sale was announced before this Sunday |
| `holiday_count` | Count of listed holidays in the week |
| `peer_median_growth` | Median `wow_growth` of the other games in the peer set |
| `peer_set_size` | How many other games were in that median |

Sienna's calendar supplies the sale and holiday flags. Sienna's peer file supplies the sets. Destiny's script joins them. Zeros are kept in `n_zeros` and dropped from `peak` when a zero sits next to normal hours, because the same zero timestamps appeared on every game in the history check.

## Start tonight, Thursday 5 November

### Destiny

1. Keep the Mac awake. The recorder runs at 5 minutes past every hour. Check it with `python3 collect/collect_once.py --status`.
2. Add Twitch keys to `.env` if they are not there, then run `python3 collect/collect_once.py` once. The status line should include `twitch ok`.
3. Download `chart-data.json` for the 19 games in `collect/games.csv` that are not already under `data/feasibility/steamcharts/`. One request per second. Save them as `{appid}.json` in that same folder.
4. Create `model/train.py` so it can read `data/processed/week_panel.csv` and fit, in this order: unchanged peak, weekday pattern, ridge, shallow XGBoost. Chronos waits until Saturday. The script must refuse to train on weeks starting 19 October or later.

### Sienna

1. Read `data/feasibility/steamcharts_resolution.txt` and write `analysis/data_notes.md`: what the three layers mean for a weekly peak, and which weeks are daily versus hourly.
2. Write `analysis/calendar.csv` with columns `date,sale_name,announced_on,holiday_name`. Cover 10 August through 15 November 2026. Include the next Steam seasonal sale only if you can point to an announcement date. Include Lunar New Year only if it falls in the window. It does not. Include weekends by rule, not by listing them.
3. Write `analysis/peers.csv` with columns `appid,peer_group`. Use a coarse group a player would recognize, such as shooter, survival, RPG, or live service. Every game in `collect/games.csv` appears once.
4. Do not fit a model.

### Soha

1. Clone the repo and create `report/draft.md` and `report/slides_outline.md`.
2. Draft, from this README and the feasibility file only: the question, why the unchanged-peak comparison exists, where Steam and SteamCharts data come from, the three history layers, the live recorder, and the limits. Leave a heading called `Results` with the sentence "Numbers arrive from model/results after Saturday."
3. The slide outline is ten minutes: question, the three data layers, the model order, a blank results slide, a blank live-week slide, limits.
4. Do not write a player count or a score that you calculated yourself.

Friday evening, 30 minutes together. Sienna shows the calendar and the peer groups. Destiny shows that `week_panel.csv` has one row per game per week. Soha reads the question aloud. After that meeting the rules above stay fixed.

## Friday 6 November

Destiny builds `data/processed/week_panel.csv` for weeks from 10 August through 1 November, plus the feature row for the week of 2–8 November with `next_peak` left empty. Join Sienna's calendar and peer files. Push the csv.

Sienna checks three games on the SteamCharts website against the csv: Counter-Strike 2 (`730`), Palworld (`1623730`), and one smaller game. Write the comparison in `analysis/table_check.md`. Then, on training weeks only, record the distribution of `log_growth`, the surge count, and the surge base rate in `analysis/eda_notes.md`. In a spreadsheet, compute the unchanged-peak error for five games and save the steps in `analysis/persistence_check.md`.

Soha turns Sienna's `data_notes.md` into the data section of the report, still without results.

## Saturday 7 November

Destiny runs the models in order. After each one, write the validation error to `model/results/validation.csv` and stop. Sienna adds one sentence to `analysis/decisions.md` before Destiny starts the next model: what the score was, and whether the model earned a place. Then Destiny scores the two historical test weeks once and saves `model/results/test.csv`. If Chronos-2 small does not install, Destiny writes the error in `model/results/chronos_note.txt` and the four models that ran are the submitted ladder.

The ladder, and the only question each step answers:

1. Unchanged peak. Predict `log_growth = 0`.
2. Weekday pattern. Repeat the recent pattern of days, then take the max.
3. Ridge, using momentum and calendar columns.
4. Shallow XGBoost, adding `peer_median_growth`. Depth stays small. A few hundred rows will memorize a deep tree.
5. Chronos-2 small, zero-shot, player history only, context cut at that Sunday.

Sienna chooses two historical weeks for the report: one where the best model beat the unchanged peak, and one where it did not. Write `analysis/case_studies.md` with the game, the week, the columns that were visible that Sunday, and the errors from `test.csv`.

Soha puts those two cases into the report and the slides in Sienna's words, with the numbers copied from `test.csv`.

## Sunday 8 November

By 21:00 Hong Kong time, Destiny runs the frozen script and writes `data/live/forecast_2026-11-09.csv` with columns `emitted_at_utc,appid,name,predicted_log_growth,predicted_peak,model_name`. Sienna checks that there are 24 games and that `emitted_at_utc` is before Monday. Soha checks that every name is in `collect/games.csv`. By 23:00 the file is pushed and nobody edits it.

The latest inputs that forecast may use are from the week of 2–8 November.

## Monday 10 November through Sunday 15 November

Soha finishes `report/draft.md` and the slides, except one line reserved for the live week. The report order is: question, data access, target and the locked rules, what Sienna found in the table, the model ladder, the historical test, the waiting live line, limits.

Sienna keeps `analysis/decisions.md` as the source Soha quotes. Destiny does not retune the model after Sunday.

The limits section says these things in plain sentences: about twelve usable weeks, 24 games, daily samples are not the true hourly peak, Twitch covers only the live week if the keys were added, SullyGnome was read by hand for at most one example, and the study does not show that a patch or a stream caused the surge.

## Monday 16 November

After 07:59 Hong Kong time, Destiny compares `data/live/forecast_2026-11-09.csv` with the recorder peaks for 9–15 November and saves `model/results/live_week.csv`. Sienna writes `analysis/live_week.md`: where the forecast matched and where it missed, using only that csv. Soha pastes that paragraph into the report and the last slide.

## Tuesday 17 November

Upload the report, the slides, `data/live/forecast_2026-11-09.csv`, and `model/results/live_week.csv`. No new model and no rewritten analysis.

## Prompts you can give an AI

Paste the matching prompt into a new chat that has this repository open. Each prompt tells the AI whose files it may touch.

### Destiny

```text
You are helping Destiny on Group 18's Steam spike forecast. Destiny builds the model and the table it reads. Do not edit analysis/ or report/. Do not invent scores.

Read README.md and collect/games.csv. The locked split is in the README: train through the week ending 4 October 2026, validate 5–18 October, historical test 19 October–1 November, live forecast for 9–15 November sealed on 8 November.

Build data/processed/week_panel.csv from data/feasibility/steamcharts/*.json, analysis/calendar.csv, and analysis/peers.csv, using the columns listed in the README. Drop isolated zero player counts from the peak, and keep them in n_zeros. A feature for week t may use only timestamps inside week t or earlier.

Then add model/train.py. Fit, in order, unchanged-peak, weekday-pattern, ridge, and shallow XGBoost. Read validation error from model/results/validation.csv before fitting the next model. Refuse to fit on weeks starting 19 October 2026 or later. After those four scores exist, try Chronos-2 small zero-shot with context cut at Sunday, and if the install fails write model/results/chronos_note.txt.

On Sunday 8 November only, write data/live/forecast_2026-11-09.csv with emitted_at_utc, appid, name, predicted_log_growth, predicted_peak, and model_name. Do not edit that file again.
```

### Sienna

```text
You are helping Sienna (Tam Hoi Wing) on Group 18's Steam spike forecast. Sienna owns the analysis. Do not edit model/, collect/, or report/. Do not fit a model. Do not invent a player count or a score. If a number is not in a file, say it is not in the file.

Read README.md and data/feasibility/steamcharts_resolution.txt. Write analysis/data_notes.md explaining the monthly, daily, and hourly layers and which weeks can be training rows.

Write analysis/calendar.csv with columns date, sale_name, announced_on, holiday_name for 10 August through 15 November 2026. A sale needs an announcement date you can name. Write analysis/peers.csv with columns appid, peer_group for every appid in collect/games.csv.

After data/processed/week_panel.csv exists, check Counter-Strike 2, Palworld, and one smaller game against the SteamCharts website and write analysis/table_check.md. On training weeks only, write analysis/eda_notes.md with the distribution of log_growth and the surge base rate. Compute the unchanged-peak error for five games by hand or in a sheet and save the steps in analysis/persistence_check.md.

When Destiny adds a row to model/results/validation.csv, add one sentence to analysis/decisions.md before the next model is fit. After model/results/test.csv exists, write analysis/case_studies.md for two weeks: one where the model beat the unchanged peak, and one where it did not. Use only columns that were known on that Sunday.

Do not scrape SullyGnome. A single page may be read by hand, with the URL and the date written down.
```

### Soha

```text
You are helping Soha on Group 18's Steam spike forecast. Soha writes the report and the slides. Do not edit model/, analysis/, collect/, or data/. Do not calculate a new metric. Copy numbers only from README.md, data/feasibility/steamcharts_resolution.txt, analysis/*.md, and model/results/*.csv. Where the file does not exist yet, leave the heading and the sentence "Waiting on <filename>."

Create report/draft.md in this order: question, why the unchanged-peak comparison is the baseline, data access, the three SteamCharts layers, the live recorder, the locked target and week split, what the analysis notes say, the model ladder, historical test results, a heading "Live week" containing only "Filled on 16 November from analysis/live_week.md", and limits.

The limits must say: about twelve usable weeks, 24 games, daily samples are not true hourly peaks, Twitch covers only the live week, SullyGnome is not a downloaded dataset, and the project does not show that a patch or a stream caused a surge.

Create report/slides_outline.md for a ten-minute talk: question, three data layers, model order, results with blanks until test.csv exists, one hit and one miss from analysis/case_studies.md, a blank live-week slide, limits.

On 16 November, paste analysis/live_week.md into the live-week section and the last slide. Do not rewrite the analysis.
```

## Recorder

The hourly recorder reads `collect/games.csv` and appends to `data/live/`. Destiny runs it. Sienna and Soha do not need to.

```bash
python3 collect/collect_once.py
python3 collect/collect_once.py --status
```

Steam player counts are collected on every run. Twitch viewer totals are collected only when `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` are set. The Mac schedule is `collect/group18.steamcollector.plist`, at 5 minutes past every hour. The computer has to be awake. Missing hours stay missing.

`collect/feasibility_steamcharts.py` rewrites `data/feasibility/steamcharts_resolution.txt` from the saved JSON. Use `--refresh` only when you intend to download again.
