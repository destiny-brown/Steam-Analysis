# Data and calendar

## SteamCharts layers

SteamCharts supplies three layers for the checked games: monthly observations
through 1 August 2026, daily observations from 9 August through 6 October,
and hourly observations from 6 October through the download date. Monthly
history is context only; the training weeks from 10 August through 28
September are daily, while later validation and test weeks are hourly.

## Calendar rules

The calendar covers 10 August through 15 November 2026. A Steam sale or event
is included only when its announcement date was public by the relevant Sunday
cutoff; the official 2026 schedule was announced on 16 January. Hong Kong
holidays in this interval are 26 September, 1 October, and 19 October.
Weekends are handled by the fixed `weekend_days = 2` feature, not listed as
holiday dates, and Lunar New Year is outside this window.

## Player chart

Open with the week starting 28 September 2026: the Steam Autumn Sale begins
on 1 October and Hong Kong National Day falls in the same week. Mark the
Sunday 4 October cutoff on the player chart; no player count is added here
until the chart is selected from the saved data.

## Data access and quality

SteamCharts supplies monthly observations through 1 August 2026, daily
observations from 9 August through 6 October, and hourly observations from 6
October onward. Monthly history is context rather than a training row. The
same zero-count timestamps appear across games, so isolated outage zeros are
retained in `n_zeros` but excluded from the peak and mean when surrounded by
ordinary observations.

The live Steam endpoint was not used for historical training. Twitch was
omitted because its API has no historical hours-watched series: it describes
streams live at request time.
Steam news is used instead through the project's saved Steam news JSON.

## Calendar rules

The calendar covers 10 August through 15 November 2026. Steam events are
included only when their announcement date was public by the relevant Sunday
cutoff; the official 2026 schedule was announced on 16 January. Hong Kong
holidays in this interval are 26 September, 1 October, and 19 October.
Weekends are handled by the fixed `weekend_days = 2` feature, not by listing
Saturday and Sunday as holidays.

## Histogram and calendar comparison

The saved training histogram contains 192 `log_growth` rows. The surge rule
identifies 5 rows, giving a base rate of 2.6%. Across the eight training
weeks, seven sale weeks averaged −0.0109 log-growth versus −0.0453 for the
one no-sale week; two holiday weeks averaged −0.0108 versus −0.0167 for the
six weeks without a listed holiday. These are descriptive associations, not
causal effects.

## Historical calendar case

### Week of 19–25 October 2026

By the Sunday cutoff on 25 October, Cooking Fest had ended on 19 October,
Next Fest was running, and the Hong Kong holiday on 19 October was known;
the schedule had been announced on 16 January. The saved
`model/results/test.csv` pools both historical test weeks, so it does not
provide a separate error for this one week: unchanged peak 0.144049 (ratio
1.0), weekday pattern 0.329979 (2.2907), ridge 0.126251 (0.8764), and
XGBoost 0.131923 (0.9158). These are pooled test errors, not a per-week
score.

## Live week

*Blank until 16 November; then copy only from `model/results/live_week.csv`.*

## Limits

The training history is short, the momentum columns are correlated, and a
calendar flag is an association rather than a causal effect. Twitch has no
usable public historical export for this model. The live-week result remains
blank until 16 November and will then be copied only from
`model/results/live_week.csv`.
