# Peer case: HELLDIVERS 2, week of 19–25 October 2026

A historical test week where the game's own momentum and its peer median
pointed in opposite directions.

## What was known on Sunday 25 October

All values are from the row `appid = 553850`, `week_start = 2026-10-19` in
`data/processed/week_panel.csv`. Each uses only timestamps up to that Sunday.

| Column | Value | Meaning |
|---|---|---|
| `peak` | 98,111 | Highest player sample, 19–25 October |
| `wow_growth` | +0.5022 | Peak about 65% higher than the week before |
| `peer_group` | coop_live_service | From `analysis/peers.csv` |
| `peer_median_growth` | −0.0371 | Median of the four peers' `wow_growth` |
| `peer_set_size` | 4 | Destiny 2, Warframe, Left 4 Dead 2, Grand Theft Auto V |
| `news_count` | 6 | Steam news posts in the week |
| `sale_next_week` | 1 | An announced Steam event in the next week |

Peer median, worked: the peers' `wow_growth` that week were Warframe −0.1253,
Destiny 2 −0.0558, Left 4 Dead 2 −0.0185, Grand Theft Auto V +0.0356. The
median of four values is the mean of the middle two:
(−0.0558 + −0.0185) / 2 = −0.0371.

The game's own momentum pointed sharply up. Its peer group pointed slightly
down.

## What happened in 26 October–1 November

`next_peak` was 59,891 and `log_growth` was −0.4936: the peak fell by about
39%. The unchanged-peak forecast therefore missed by 0.4936 in log growth.

The peer median had the right direction but was far too small: it implied
roughly a 4% fall, not a 39% fall. The week looks like a one-week spike that
did not last. This case shows a pattern, not a cause: the panel does not say
why HELLDIVERS 2 rose or fell.

## Model errors

| Model | Error for this row | Source |
|---|---|---|
| Unchanged peak | 0.4936 | Absolute value of `log_growth` (−0.4936) in `week_panel.csv` |
| Chronos-2 small, zero-shot | 0.3773 | Row for 553850, week 2026-10-19, in `model/results/chronos_note.txt` (predicted −0.1163) |
| Ridge | not saved per row | `model/results/test.csv` holds only the pooled error |
| XGBoost | not saved per row | `model/results/test.csv` holds only the pooled error |

For comparison, the pooled test errors in `model/results/test.csv` (both test
weeks, 48 rows) are: unchanged peak 0.1440, weekday pattern 0.3300, Ridge
0.1263, XGBoost 0.1319. This one row's unchanged-peak error, 0.4936, is more
than three times the pooled figure: HELLDIVERS 2 is one of the largest
misses in the test weeks.

Chronos-2, which sees only the game's own player history, predicted a fall of
about 11%: the right direction, but still far short of the 39% fall. Like the
peer median, it had the direction but not the size.

This row's outcome week (26 October–1 November) was complete when the test
was scored, so the note in `analysis/peer_notes.md` about the second test
week does not affect it.
