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

*Pending Destiny's training-week histogram, surge rule/base rate, and the
sale/holiday comparison from the saved model outputs. No score is reported
until those files exist.*

## Historical calendar case

*Pending a test-week case copied from `test.csv`; only features known by that
Sunday will be used.*

## Limits

The training history is short, the momentum columns are correlated, and a
calendar flag is an association rather than a causal effect. Twitch has no
usable public historical export for this model. The live-week result will be
added after the sealed forecast is scored on 16 November.
