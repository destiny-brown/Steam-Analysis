# Sienna slides

## 1. Player chart

Open with the week starting 28 September 2026: the Steam Autumn Sale begins
on 1 October and Hong Kong National Day falls in the same week; mark the
Sunday 4 October cutoff.

## 2. Data quality

- SteamCharts has monthly, daily, and hourly layers; monthly history is context.
- Shared zero timestamps are treated as outages in peak/mean calculations.
- Steam news replaces Twitch as the historical attention input.

## 3. Histogram and surge rule

The saved training histogram contains 192 training log-growth rows. The surge
rule identifies 5 rows, giving a base rate of 2.6%.

## 4. Calendar comparison

The calendar uses announced Steam events and Hong Kong public holidays. The
official 2026 Steam schedule was public on 16 January; the holiday dates in
the feature interval are 26 September, 1 October, and 19 October.

Across the eight training weeks, seven sale weeks averaged −0.0109
log-growth versus −0.0453 for the one no-sale week. Two holiday weeks
averaged −0.0108 versus −0.0167 for six non-holiday weeks. These are
descriptive associations, not causal effects.

## 5. Calendar case

For the week of 19–25 October, Next Fest and the 19 October Hong Kong
holiday were already known by the Sunday cutoff. `test.csv` pools both
historical test weeks, so its errors are not a per-week score: unchanged
peak 0.144049, weekday pattern 0.329979, ridge 0.126251, and XGBoost
0.131923.

## 6. Live week

Leave blank until 16 November; then copy only from `live_week.csv`.
