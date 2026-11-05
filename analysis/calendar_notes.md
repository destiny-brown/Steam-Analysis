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
October, and hourly points from 6 October onward. Therefore the project weeks
starting 10 August through 28 September are daily, and weeks starting 5
October through 2 November are hourly. The 2 November row is the live feature
week and is incomplete at the Sunday cutoff.

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

## Results still to be copied from Destiny's outputs

Do not invent scores here. After the model run, copy the training-week
histogram, surge rule/base rate, and the sale-week versus ordinary-week and
holiday-week versus ordinary-week summaries from Destiny's saved outputs.
The three SteamCharts spot checks required by the README should record the
SteamCharts page URL, checked date, and observed series resolution for appids
730, 1623730, and one smaller game.
