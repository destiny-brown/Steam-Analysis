# Sienna slides

## 1. Player chart

*[Placeholder: insert a recognizable player chart for the week of 28
September 2026 and mark the Sunday 4 October cutoff.]*

## 2. Data quality

- SteamCharts has monthly observations through 1 August, daily observations
  from 9 August through 6 October, and hourly observations from 6 October
  onward.
- Monthly history is context; the training weeks are daily.
- Twitch was omitted because its API has no historical hours-watched series.

## 3. Training histogram and surge rule

*[Placeholder: insert the training-week `log_growth` histogram with the surge
rule marked.]*

The surge count is 5 of 192 training rows, for a base rate of 2.6%.

## 4. Calendar comparison

The seven sale weeks averaged −0.0109 log-growth versus −0.0453 for the one
no-sale training week. The two holiday weeks averaged −0.0108 versus −0.0167
for the six non-holiday weeks. These are descriptive associations, not causal
effects.

## 5. Calendar case study

In the week of 19–25 October, Next Fest and the 19 October Hong Kong holiday
were known by the Sunday cutoff, with the schedule announced on 16 January
2026. The pooled test errors were unchanged peak 0.144049, weekday pattern
0.329979, ridge 0.126251, and XGBoost 0.131923; these are not per-week
scores.

## 6. Live week
