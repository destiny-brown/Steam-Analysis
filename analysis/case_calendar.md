# Calendar case

## Week of 19–25 October 2026

By Sunday 25 October, the public calendar information included Cooking Fest
ending on 19 October, Next Fest running from 19–25 October, and the Hong Kong
holiday on 19 October (the day following Chung Yeung Festival); all were
announced on 16 January 2026. The columns known on that Sunday were
`appid`, `name`, `week_start`, `resolution`, `n_samples`, `n_zeros`, `peak`,
`mean_players`, `wow_growth`, `growth_4w`, `median_4w`, `mad_4w`,
`weekend_days`, `sale_this_week`, `sale_next_week`, `holiday_count`,
`peer_median_growth`, `peer_set_size`, `news_count`, `days_since_news`,
`major_update`, and `days_since_major_update`; `next_peak` and `log_growth`
were not yet known.

The saved `model/results/test.csv` provides exact errors pooled across the
weeks of 19–25 October and 26 October–1 November, not a separate error for
this one week:

| Model | Test MAE | Ratio to unchanged-peak |
| --- | ---: | ---: |
| unchanged_peak | 0.144049 | 1.0 |
| weekday_pattern | 0.329979 | 2.2907 |
| ridge | 0.126251 | 0.8764 |
| xgboost | 0.131923 | 0.9158 |

These are copied directly from `test.csv` and must not be interpreted as
per-week scores.
