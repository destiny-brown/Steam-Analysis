# Group 18 — Steam player spike forecast

On Sunday night, using only information already public, can we forecast next week's peak Steam player count better than assuming the peak will not change?

Repository: https://github.com/destiny-brown/Steam-Analysis

Submission is **Tuesday 17 November 2026**. The forecast file for the week of 9–15 November is sealed by **23:00 Hong Kong time on Sunday 8 November**. That file is not edited after it is saved. The week is scored on **Monday 16 November**, after 07:59 Hong Kong time, when the recorded week is complete. Tuesday is for uploading.

## Team

| Person | Owns | Does not own |
| --- | --- | --- |
| Destiny | The model code, the week-table script, the news download, and the hourly recorder | Calendar research, peer groups, report prose, slides |
| Sienna (Tam Hoi Wing) | Sales, holidays, and the calendar half of the report and slides | Peer groups, fitting models |
| Soha | Peer groups, peer momentum, and the peer half of the report and slides | The sale calendar, fitting models |

Sienna and Soha write the report together. They use separate files so a push does not overwrite the other person.

| Person | Files |
| --- | --- |
| Destiny | `model/`, `collect/`, `data/` |
| Sienna | `analysis/calendar.csv`, `analysis/calendar_notes.md`, `analysis/decisions_calendar.md`, `report/02_data_and_calendar.md`, `report/slides_sienna.md` |
| Soha | `analysis/peers.csv`, `analysis/peer_notes.md`, `analysis/decisions_peers.md`, `report/01_question_and_peers.md`, `report/slides_soha.md` |

```bash
git pull
# edit only your own files from the table above
git add analysis/calendar.csv   # example: add the files you changed
git commit -m "Describe the change in one sentence."
git push
```

If `git push` is rejected, run `git pull` and push again. Do not edit another person's file to make the push work.

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
- Twitch is not a model input. The API only shows live streams, and SullyGnome has no public export. Attention inside the model is Steam news: how many posts fell in the week, and how many days since the previous post.
- SullyGnome may be opened in a browser for one case study. Copy the numbers by hand with the page URL and the date. Do not scrape it.
- Do not invent a metric, a player count, or a model score. If a file does not contain the number, the report says the number is not in yet.

SteamCharts history, already measured in `data/feasibility/steamcharts_resolution.txt`, has three layers on every game we checked: monthly through 1 August 2026, daily from 9 August through 6 October, and hourly from 6 October. About twelve weeks can train a weekly model. Monthly history is context, not a training row.

## Twitch

Leave Twitch out of the model. Helix can describe a stream that is live at the moment you ask, and it cannot return last August's hours watched. SullyGnome stores that history, and it has no public API. Building a developer application for a feature the training table cannot use would spend the night before Sunday on data that starts too late.

Steam news replaces it. `ISteamNews/GetNewsForApp` returns patch and event posts with publication times, for the same weeks as the player history. The model sees `news_count` and `days_since_news`. If one case-study week looks like a streaming event, Sienna may open that game's SullyGnome page, write down the hours watched by hand, and Soha can quote that page as an illustration. Those figures never enter `week_panel.csv`.

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
| `news_count` | Steam news posts with a publication time inside the week |
| `days_since_news` | Days from the Sunday cutoff back to the latest post on or before that Sunday |

Sienna's calendar supplies the sale and holiday flags. Soha's peer file supplies the sets. Destiny's script joins both. Zeros are kept in `n_zeros` and dropped from `peak` when a zero sits next to normal hours, because the same zero timestamps appeared on every game in the history check.

## Start tonight, Thursday 5 November

### Destiny

1. Keep the Mac awake. The recorder runs at 5 minutes past every hour. Check it with `python3 collect/collect_once.py --status`. Steam counts are enough. Do not spend tonight on a Twitch developer application.
2. Download `chart-data.json` for the 19 games in `collect/games.csv` that are not already under `data/feasibility/steamcharts/`. One request per second. Save them as `{appid}.json` in that same folder.
3. Pull Steam news for the same 24 games from `ISteamNews/GetNewsForApp` and save the raw JSON under `data/news/`. Count posts by week from the publication timestamps.
4. Create `model/train.py` so it can read `data/processed/week_panel.csv` and fit, in this order: unchanged peak, weekday pattern, ridge, shallow XGBoost. Chronos waits until Saturday. The script must refuse to train on weeks starting 19 October or later.

### Sienna

1. Read `data/feasibility/steamcharts_resolution.txt`. Write `analysis/calendar_notes.md`: which of the training weeks are daily, which are hourly, and which sales or holidays fall inside them.
2. Write `analysis/calendar.csv` with columns `date,sale_name,announced_on,holiday_name`. Cover 10 August through 15 November 2026. A sale needs an announcement date you can name. Lunar New Year is not in this window. Weekends are a rule, not a list of dates.
3. Start `report/02_data_and_calendar.md` with the three SteamCharts layers and the calendar rules. Leave results blank.
4. Do not fit a model, and do not edit `analysis/peers.csv`.

### Soha

1. Write `analysis/peers.csv` with columns `appid,peer_group`. Every game in `collect/games.csv` appears once. Use a group a player would recognize, such as shooter, survival, RPG, or live service. A group needs at least three games. If it does not, say so in the notes and use a broader group.
2. Write `analysis/peer_notes.md`: peer momentum is the median week-to-week log growth of the other games in the group, leaving the game itself out.
3. Start `report/01_question_and_peers.md` with the question, why the unchanged-peak comparison exists, and how peer momentum is defined. Leave results blank.
4. Do not fit a model, and do not edit `analysis/calendar.csv`.

Friday evening, 30 minutes together. Sienna shows the calendar. Soha shows the peer groups. Destiny shows that `week_panel.csv` joins both files. After that meeting the rules above stay fixed.

## Friday 6 November

Destiny builds `data/processed/week_panel.csv` for weeks from 10 August through 1 November, plus the feature row for the week of 2–8 November with `next_peak` left empty. Join Sienna's calendar and Soha's peer file. Push the csv.

Sienna, on training weeks only, compares sale weeks and holiday weeks with ordinary weeks. Write the player-growth difference in `analysis/calendar_notes.md`. Check three sale or holiday dates against the SteamCharts page for Counter-Strike 2 (`730`), Palworld (`1623730`), and one smaller game.

Soha, on training weeks only, checks whether a game's growth moves with its peers. Write the comparison in `analysis/peer_notes.md`, including five games where you also compute the unchanged-peak error by hand. Count how often the peer median and the game move in the same direction.

## Saturday 7 November

Destiny runs the models in order. After each one, write the validation error to `model/results/validation.csv` and stop. Before the next model starts, Sienna adds one sentence to `analysis/decisions_calendar.md` about the calendar columns, and Soha adds one sentence to `analysis/decisions_peers.md` about the peer column. Then Destiny scores the two historical test weeks once and saves `model/results/test.csv`. If Chronos-2 small does not install, Destiny writes the error in `model/results/chronos_note.txt` and the four models that ran are the submitted ladder.

The ladder, and the only question each step answers:

1. Unchanged peak. Predict `log_growth = 0`.
2. Weekday pattern. Repeat the recent pattern of days, then take the max.
3. Ridge, using momentum and calendar columns.
4. Shallow XGBoost, adding `peer_median_growth`. Depth stays small. A few hundred rows will memorize a deep tree.
5. Chronos-2 small, zero-shot, player history only, context cut at that Sunday.

Sienna writes one case in `analysis/case_calendar.md`: a week where a sale or holiday was already public on Sunday, with the errors copied from `test.csv`. Soha writes one case in `analysis/case_peers.md`: a week where the peer median and the game agreed, or a week where they did not. Each case uses only columns that were known that Sunday. Each person puts their own case into their own report file and their own slides.

## Sunday 8 November

By 21:00 Hong Kong time, Destiny runs the frozen script and writes `data/live/forecast_2026-11-09.csv` with columns `emitted_at_utc,appid,name,predicted_log_growth,predicted_peak,model_name`. Sienna checks that there are 24 games and that `emitted_at_utc` is before Monday. Soha checks that every name matches `collect/games.csv` and that each game's peer group is the one in `analysis/peers.csv`. By 23:00 the file is pushed and nobody edits it.

The latest inputs that forecast may use are from the week of 2–8 November.

## Monday 10 November through Sunday 15 November

Sienna finishes `report/02_data_and_calendar.md` and `report/slides_sienna.md`: data layers, calendar, her case study, and a blank live-week line. Soha finishes `report/01_question_and_peers.md` and `report/slides_soha.md`: question, peer momentum, her case study, and a blank live-week line. On Sunday 15 November they read both drafts once and agree the spoken order: question, data, calendar, peers, model ladder, two cases, blank live week, limits. Destiny does not retune the model after Sunday 8 November.

The limits section says these things in plain sentences: about twelve usable weeks, 24 games, daily samples are not the true hourly peak, Twitch was left out because it has no history the model can train on, Steam news is the attention signal instead, SullyGnome was read by hand for at most one example, and the study does not show that a patch or a stream caused the surge.

## Monday 16 November

After 07:59 Hong Kong time, Destiny compares `data/live/forecast_2026-11-09.csv` with the recorder peaks for 9–15 November and saves `model/results/live_week.csv`. Sienna writes the calendar sentence in `report/02_data_and_calendar.md`. Soha writes the peer sentence in `report/01_question_and_peers.md`. Both use only `live_week.csv`. They put those two sentences on the last slides.

## Tuesday 17 November

Upload the report, the slides, `data/live/forecast_2026-11-09.csv`, and `model/results/live_week.csv`. No new model and no rewritten analysis.

## Prompts you can give an AI

Paste the matching prompt into a new chat that has this repository open. Each prompt tells the AI whose files it may touch.

### Destiny

```text
You are helping Destiny on Group 18's Steam spike forecast. Destiny builds the model and the table it reads. Do not edit analysis/ or report/. Do not invent scores.

Read README.md and collect/games.csv. The locked split is in the README: train through the week ending 4 October 2026, validate 5–18 October, historical test 19 October–1 November, live forecast for 9–15 November sealed on 8 November.

Build data/processed/week_panel.csv from data/feasibility/steamcharts/*.json, data/news/*.json, analysis/calendar.csv, and analysis/peers.csv, using the columns listed in the README. Include news_count and days_since_news. Do not add Twitch columns. Drop isolated zero player counts from the peak, and keep them in n_zeros. A feature for week t may use only timestamps inside week t or earlier.

Then add model/train.py. Fit, in order, unchanged-peak, weekday-pattern, ridge, and shallow XGBoost. Read validation error from model/results/validation.csv before fitting the next model. Refuse to fit on weeks starting 19 October 2026 or later. After those four scores exist, try Chronos-2 small zero-shot with context cut at Sunday, and if the install fails write model/results/chronos_note.txt.

On Sunday 8 November only, write data/live/forecast_2026-11-09.csv with emitted_at_utc, appid, name, predicted_log_growth, predicted_peak, and model_name. Do not edit that file again.
```

### Sienna

```text
You are helping Sienna (Tam Hoi Wing) on Group 18's Steam spike forecast. Sienna owns sales, holidays, and her half of the report. Do not edit model/, collect/, data/, analysis/peers.csv, analysis/peer_notes.md, or report/01_question_and_peers.md. Do not fit a model. Do not invent a player count or a score.

Read README.md and data/feasibility/steamcharts_resolution.txt. Write analysis/calendar_notes.md on which training weeks are daily or hourly and which sales or holidays fall in them. Write analysis/calendar.csv with columns date, sale_name, announced_on, holiday_name for 10 August through 15 November 2026. A sale needs an announcement date you can name.

After data/processed/week_panel.csv exists, compare sale and holiday weeks with ordinary training weeks and add that comparison to analysis/calendar_notes.md. Check three of those dates against the SteamCharts page for appids 730, 1623730, and one smaller game.

When model/results/validation.csv gains a row, add one sentence to analysis/decisions_calendar.md about the calendar columns. After model/results/test.csv exists, write one case in analysis/case_calendar.md for a week when a sale or holiday was already public, using only columns known that Sunday, and copy the errors from test.csv.

Write report/02_data_and_calendar.md and report/slides_sienna.md from those files. Leave the live-week line blank until 16 November, then fill it from model/results/live_week.csv only.
```

### Soha

```text
You are helping Soha on Group 18's Steam spike forecast. Soha owns peer groups, peer momentum, and her half of the report. Do not edit model/, collect/, data/, analysis/calendar.csv, analysis/calendar_notes.md, or report/02_data_and_calendar.md. Do not fit a model. Do not invent a player count or a score.

Read README.md and collect/games.csv. Write analysis/peers.csv with columns appid, peer_group. Every appid appears once. A group needs at least three games. Write analysis/peer_notes.md defining peer momentum as the median week-to-week log growth of the other games in the group.

After data/processed/week_panel.csv exists, measure on training weeks how often a game's log growth moves in the same direction as peer_median_growth. Also compute the unchanged-peak error for five games by hand and save the steps in analysis/peer_notes.md.

When model/results/validation.csv gains a row, add one sentence to analysis/decisions_peers.md about the peer column. After model/results/test.csv exists, write one case in analysis/case_peers.md where the peer median and the game agreed, or where they did not. Use only columns known that Sunday, and copy the errors from test.csv.

Write report/01_question_and_peers.md and report/slides_soha.md from those files. Include the limits: about twelve usable weeks, 24 games, daily samples are not true hourly peaks, Twitch is not in the model, and the project does not show that a patch or a peer game caused a surge. Leave the live-week line blank until 16 November, then fill it from model/results/live_week.csv only.
```

## Recorder

The hourly recorder reads `collect/games.csv` and appends to `data/live/`. Destiny runs it. Sienna and Soha do not need to.

```bash
python3 collect/collect_once.py
python3 collect/collect_once.py --status
```

Steam player counts are collected on every run. Twitch collection stays switched off. The Mac schedule is `collect/group18.steamcollector.plist`, at 5 minutes past every hour. The computer has to be awake. Missing hours stay missing.

`collect/feasibility_steamcharts.py` rewrites `data/feasibility/steamcharts_resolution.txt` from the saved JSON. Use `--refresh` only when you intend to download again.
