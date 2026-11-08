# Calendar case

## Week of 19–25 October 2026

By the Sunday cutoff on 25 October, the calendar already contained Cooking
Fest through 19 October, Next Fest from 19 October, and the Hong Kong holiday
on 19 October (the day following Chung Yeung Festival). Each event's
announcement date was 16 January 2026, so these columns were available before
the cutoff.

The saved `model/results/test.csv` reports errors pooled across both historical
test weeks (19–25 October and 26 October–1 November), rather than separately
for this one week:

| Model | Test MAE | Ratio to unchanged-peak |
| --- | ---: | ---: |
| unchanged peak | 0.144049 | 1.0 |
| weekday pattern | 0.329979 | 2.2907 |
| ridge | 0.126251 | 0.8764 |
| XGBoost | 0.131923 | 0.9158 |

This case therefore illustrates the calendar information known on 25 October,
while the saved errors should not be read as a per-week score.
