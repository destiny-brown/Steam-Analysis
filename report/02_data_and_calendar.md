# Data and calendar

## Player chart

*Pending Destiny's chosen player chart and the Sunday cutoff marker.*

## Data access and quality

SteamCharts supplies monthly observations through 1 August 2026, daily
observations from 9 August through 6 October, and hourly observations from 6
October onward. Monthly history is context rather than a training row. The
same zero-count timestamps appear across games, so isolated outage zeros are
retained in `n_zeros` but excluded from the peak and mean when surrounded by
ordinary observations.

The live Steam endpoint was not used for historical training. Twitch was
refused as a model input because its API describes streams live at request
time and does not provide the historical hours-watched series needed here.
Steam news is used instead through the project's saved Steam news JSON.

## Calendar rules

The calendar covers 10 August through 15 November 2026. Steam events are
included only when their announcement date was public by the relevant Sunday
cutoff; the official 2026 schedule was announced on 16 January. Hong Kong
holidays in this interval are 26 September, 1 October, and 19 October.
Weekends are handled by the fixed `weekend_days = 2` feature, not by listing
Saturday and Sunday as holidays.

## Histogram and calendar comparison

The saved `model/results/log_growth_histogram.png` is the training histogram;
the panel has 192 training log-growth rows. The surge count and base rate are
not stated because no saved tabular output contains them.

For the eight training weeks from 10 August through 28 September, the seven
sale weeks (`sale_this_week = 1`) had mean log-growth −0.0109, compared with
−0.0453 for the one no-sale week. The two holiday weeks had mean log-growth
−0.0108, compared with −0.0167 for the six weeks without a listed holiday.
These are descriptive associations from a short sample, not causal effects.

## Historical calendar case

*Pending a test-week case copied from `test.csv`; only features known by that
Sunday will be used.*

## Limits

The training history is short, the momentum columns are correlated, and a
calendar flag is an association rather than a causal effect. Twitch has no
usable public historical export for this model. The live-week result remains
blank until 16 November and will then be copied only from
`model/results/live_week.csv`.
