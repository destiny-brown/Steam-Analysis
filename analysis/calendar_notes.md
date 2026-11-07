# Calendar notes

## Scope and sources

The calendar covers the feature interval 10 August through 15 November 2026.
Rows are event or holiday dates; dates with no listed event are ordinary
calendar dates. Sundays are not repeated here because the project defines
weekends as a fixed rule (`weekend_days = 2`), not as holiday rows.

Steam event dates and their public announcement date come from Valve's
[Steamworks 2026 second-half schedule](https://steamcommunity.com/groups/steamworks/announcements/detail/493837645658461608?pubDate=20260116).
The schedule was public on 16 January 2026, before every project cutoff in
this interval. The calendar includes the official Fests and the Autumn Sale
because the README asks for announced Steam sales/events that fall in a week.

Holiday dates come from the Hong Kong government's
[2026 general-holiday list](https://www.gov.hk/en/about/abouthk/holiday/2026.htm):
26 September (the day following the Chinese Mid-Autumn Festival), 1 October
(National Day), and 19 October (the day following Chung Yeung Festival).
Lunar New Year is outside the feature interval. No weekend is added as a
separate holiday row.

## SteamCharts layers

The feasibility check reports the same three layers for every checked game:
monthly points through 1 August, daily points from 9 August through 6
October, and hourly points from 6 October onward. Therefore every training week, starting 10 August through 28 September, is
daily. No hourly week is in the training set: the weeks starting 5 October
and 12 October are validation weeks, and the weeks starting 19 October and
26 October are historical test weeks; all four are hourly. The 2 November
row is the live feature week and is incomplete at the Sunday cutoff.

## Weeks and calendar flags

| Week start | Resolution | Calendar items |
| --- | --- | --- |
| 2026-08-10 | daily | Cyberpunk Fest ends on 10 August |
| 2026-08-17 | daily | Pins & Pegs Fest |
| 2026-08-31 | daily | PvE Survival Crafting Fest |
| 2026-09-07 | daily | Programming Fest begins on 10 September |
| 2026-09-14 | daily | Programming Fest; Party-Based RPG Fest |
| 2026-09-21 | daily | Party-Based RPG Fest; 26 September holiday |
| 2026-09-28 | daily | Steam Autumn Sale begins 1 October; National Day |
| 2026-10-05 | hourly | Steam Autumn Sale ends 8 October |
| 2026-10-12 | hourly | Cooking Fest |
| 2026-10-19 | hourly | Cooking Fest ends; Next Fest; 19 October holiday |
| 2026-10-26 | hourly | Next Fest ends; Steam Scream V Fest |
| 2026-11-02 | hourly | No listed sale or holiday; live feature week |

The panel builder applies `announced_on <= Sunday cutoff` before setting
`sale_this_week` or `sale_next_week`. All sale rows above satisfy that rule.
Holiday rows are counted by week; the 26 September, 1 October, and 19
October dates therefore contribute one holiday each.

## Training comparison

The training interval is the eight feature weeks starting 10 August through
28 September (192 game-weeks). Using `log_growth` from
`data/processed/week_panel.csv`, the seven weeks with `sale_this_week = 1`
have mean log-growth −0.0109 and mean absolute log-growth 0.1170. The one
training week with `sale_this_week = 0` has mean log-growth −0.0453 and mean
absolute log-growth 0.0941. This is a descriptive comparison, not a causal
sale effect; the no-sale reference is only one week.

The two holiday weeks have mean log-growth −0.0108 and mean absolute
log-growth 0.1022. The six weeks without a listed holiday have mean
log-growth −0.0167 and mean absolute log-growth 0.1181. Holiday weeks are
therefore close to ordinary weeks in this short sample.

The saved `model/results/log_growth_histogram.png` is the training log-growth
histogram. The surge count is 5 out of 192 training rows, for a base rate of
2.6%.

## SteamCharts spot checks

The SteamCharts pages were checked on 7 November 2026 for three calendar
dates. The page checks confirm that each date falls in the published series;
the hourly layer begins on 6 October.

| Calendar date | Item | App | Page | Observed resolution |
| --- | --- | --- | --- | --- |
| 2026-09-26 | Day following Chinese Mid-Autumn Festival | Counter-Strike 2 (730) | https://steamcharts.com/app/730 | daily |
| 2026-10-01 | Steam Autumn Sale and National Day | Palworld (1623730) | https://steamcharts.com/app/1623730 | daily |
| 2026-10-19 | Cooking Fest, Next Fest, and holiday | Valheim (892970) | https://steamcharts.com/app/892970 | hourly |

These checks agree with the saved feasibility report: monthly history ends 1
August, daily history runs 9 August–6 October, and hourly history starts 6
October.

## Opening week

Open the talk with the week starting 28 September 2026: the Steam Autumn Sale
begins on 1 October and Hong Kong National Day falls in the same week. It is
a recognizable calendar case and still belongs to the daily training layer.
