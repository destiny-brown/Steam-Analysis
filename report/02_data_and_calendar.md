# Data and calendar

## 1. Player chart

*[Placeholder: insert a recognizable player chart for the week of 28
September 2026 and mark the Sunday 4 October cutoff.]*

## 2. Data quality

SteamCharts provides three layers in the checked histories: monthly
observations through 1 August 2026, daily observations from 9 August through
6 October, and hourly observations from 6 October through the download date.
Monthly observations are context rather than training rows; the training
weeks from 10 August through 28 September are daily.

Twitch was omitted because its API has no historical hours-watched series. It
describes streams live at request time, so it cannot provide the historical
attention measure required for this model.

## 3. Training histogram and surge rule

*[Placeholder: insert the training-week histogram of `log_growth` with the
surge rule marked.]*

The surge rule identifies 5 of 192 training rows, giving a base rate of 2.6%.

## 4. Calendar comparison

Across the eight training weeks, the seven sale weeks had mean log-growth
−0.0109 and mean absolute log-growth 0.1170, compared with −0.0453 and
0.0941 for the one training week without a sale. The two holiday weeks had
mean log-growth −0.0108 and mean absolute log-growth 0.1022, compared with
−0.0167 and 0.1181 for the six weeks without a listed holiday. These are
descriptive associations from a short sample, not causal effects.

## 5. Calendar case study

For the week of 19–25 October 2026, Cooking Fest had ended, Next Fest was
running, and the 19 October Hong Kong holiday was known by the Sunday cutoff;
all were announced on 16 January 2026. The known feature columns were
`appid`, `name`, `week_start`, `resolution`, `n_samples`, `n_zeros`, `peak`,
`mean_players`, `wow_growth`, `growth_4w`, `median_4w`, `mad_4w`,
`weekend_days`, `sale_this_week`, `sale_next_week`, `holiday_count`,
`peer_median_growth`, `peer_set_size`, `news_count`, `days_since_news`,
`major_update`, and `days_since_major_update`; `next_peak` and `log_growth`
were not known on that Sunday.

The saved test results pool both historical test weeks, so they are not
per-week scores: unchanged peak 0.144049 (ratio 1.0), weekday pattern
0.329979 (2.2907), ridge 0.126251 (0.8764), and XGBoost 0.131923 (0.9158).

## 6. Live week
