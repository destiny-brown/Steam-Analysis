# Sienna slides

## 1. Player chart

*Pending Destiny's chart and Sunday cutoff marker.*

## 2. Data quality

- SteamCharts has monthly, daily, and hourly layers; monthly history is context.
- Shared zero timestamps are treated as outages in peak/mean calculations.
- Steam news replaces Twitch as the historical attention input.

## 3. Histogram and surge rule

The saved training histogram contains 192 training log-growth rows. The surge
count and base rate are not yet in a saved tabular output.

## 4. Calendar comparison

The calendar uses announced Steam events and Hong Kong public holidays. The
official 2026 Steam schedule was public on 16 January; the holiday dates in
the feature interval are 26 September, 1 October, and 19 October.

Across the eight training weeks, seven sale weeks averaged −0.0109
log-growth versus −0.0453 for the one no-sale week. Two holiday weeks
averaged −0.0108 versus −0.0167 for six non-holiday weeks. These are
descriptive associations, not causal effects. The test case remains blank
until `test.csv` exists.

## 5. Live week

Leave blank until 16 November; then copy only from `live_week.csv`.
