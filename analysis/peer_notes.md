# Peer groups and peer momentum

Owner: Soha. Groups are in `analysis/peers.csv`. Destiny's script computes
`peer_median_growth` and `peer_set_size` from that file; I do not compute
them myself.

## The five groups

Each group is one a player would recognise. Every one of the 24 games in
`collect/games.csv` appears exactly once. Every group has at least four
games, so each game always has at least three peers once it is left out.

| peer_group | Games | Size |
|---|---|---|
| shooter | Counter-Strike 2, PUBG: BATTLEGROUNDS, Apex Legends, Team Fortress 2, Marvel Rivals, THE FINALS | 6 |
| coop_live_service | Destiny 2, Warframe, HELLDIVERS 2, Left 4 Dead 2, Grand Theft Auto V | 5 |
| survival_sandbox | Rust, Valheim, Palworld, Terraria, Stardew Valley | 5 |
| rpg | ELDEN RING, Baldur's Gate 3, Path of Exile, Lost Ark | 4 |
| pvp_other | Dota 2, Dead by Daylight, War Thunder, NARAKA: BLADEPOINT | 4 |

### Judgement calls

- **Destiny 2** is a shooter, but it is placed in `coop_live_service`
  because its player count follows seasons and expansions like Warframe and
  HELLDIVERS 2, not competitive PvP seasons.
- **Grand Theft Auto V** is in `coop_live_service` because most current
  Steam players are in GTA Online, which runs on weekly event updates.
- **Stardew Valley** is a farming game, grouped with sandbox games because
  it shares their slow, long-tail, update-driven player pattern.
- **pvp_other** is the broader group the README allows. Dota 2 (MOBA),
  Dead by Daylight (asymmetric horror), War Thunder (vehicle combat) and
  NARAKA (melee battle royale) each lacked two similar games in the list,
  so no narrower group of three was possible. They share competitive PvP
  play that is not a gunfight shooter.
- **Path of Exile** and **Lost Ark** are action RPGs; ELDEN RING and
  Baldur's Gate 3 are single-player-first RPGs. A narrower split would give
  groups of two, so they share the broader `rpg` group.

## Definition of peer momentum

For game *g* in group *G* and feature week *t*:

```
wow_growth(h, t)          = log(peak(h, t)) - log(peak(h, t-1))
peer_median_growth(g, t)  = median of wow_growth(h, t) for every h in G, h ≠ g
peer_set_size(g, t)       = number of games h that entered that median
```

In words: peer momentum is the median week-to-week log growth of the
**other** games in the group, leaving the game itself out.

- **Leave-one-out.** The game's own growth is excluded, so the feature does
  not repeat `wow_growth`, which the model already sees.
- **Median, not mean.** One peer with a launch or an outage would pull a
  mean; the median of three to five games is more stable.
- **Known at Sunday.** `wow_growth(h, t)` uses only weeks *t* and *t-1*, so
  the feature is known at the Sunday cutoff and predicts week *t+1* without
  lookahead.
- **Missing peers.** If a peer has no `wow_growth` that week (for example
  its first week), it is dropped from the median and `peer_set_size` shows
  the smaller count.

## Training-week comparison

Source: `data/processed/week_panel.csv` as rebuilt by Destiny on 6 November
with this `peers.csv` (commit a1cdfe2). Training weeks are the feature weeks
starting 10 August through 28 September (192 game-weeks). The week starting
10 August has no previous week, so its `wow_growth` and
`peer_median_growth` are set to 0; it is left out below, which leaves
**168 game-weeks** (7 weeks x 24 games). No row had a growth of exactly 0
after that.

### Do games move with their peers?

| Comparison | Same direction | Share |
|---|---|---|
| Same week: game `wow_growth` vs `peer_median_growth` | 110 of 168 | 65.5% |
| Next week: game `log_growth` vs `peer_median_growth` | 92 of 168 | 54.8% |
| Reference: game `log_growth` vs its own `wow_growth` | 90 of 168 | 53.6% |
| Reference: always guess "down" | 105 of 168 | 62.5% |

By group, next-week agreement was: rpg 24/28, survival_sandbox 21/35,
coop_live_service 19/35, pvp_other 16/28, shooter 12/42.

Correlation between `peer_median_growth` and the game's growth was 0.059 in
the same week and −0.054 for the next week.

**Reading.** In the same week, a game moves in its peers' direction about two
times in three, so the groups do describe shared movement. As a forecast of
next week the peer median is barely better than a coin flip and does worse
than simply guessing "down": 62.5% of training game-weeks fell, and the peer
median was negative in 79% of rows, so most of its agreement is the general
downward drift of August–September. Agreement is strong only in the RPG group
and below chance for shooters. This is a descriptive count on eight daily
weeks, not evidence that a peer game causes a change.

### Five unchanged-peak errors worked by hand

The unchanged-peak forecast predicts `log_growth = 0`, so its error for one
game-week is |ln(next_peak / peak)|. Week starting 21 September 2026 (a
training week), one game from each peer group. `peak` and `next_peak` are
copied from `week_panel.csv`; the steps were then recomputed on a
calculator.

| Game | peak (21–27 Sep) | next_peak (28 Sep–4 Oct) | next_peak / peak | ln(ratio) | Error |
|---|---|---|---|---|---|
| Counter-Strike 2 | 1,450,705 | 1,314,127 | 0.90585 | −0.0989 | 0.0989 |
| Destiny 2 | 37,341 | 40,811 | 1.09293 | +0.0889 | 0.0889 |
| Palworld | 82,413 | 78,690 | 0.95483 | −0.0462 | 0.0462 |
| Baldur's Gate 3 | 72,504 | 71,090 | 0.98050 | −0.0197 | 0.0197 |
| Dota 2 | 897,660 | 889,598 | 0.99102 | −0.0090 | 0.0090 |

Mean of the five errors: (0.0989 + 0.0889 + 0.0462 + 0.0197 + 0.0090) / 5 =
**0.0525**. Each ln(ratio) matches the `log_growth` value in the panel to
four decimals. An error of 0.0989 means Counter-Strike 2's peak was about 9%
lower than the unchanged forecast; Dota 2 was within 1%.
