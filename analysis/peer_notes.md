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

*Not in yet. Added after `data/processed/week_panel.csv` is checked on
training weeks: how often a game's `log_growth` has the same sign as
`peer_median_growth`, plus five unchanged-peak errors worked by hand.*
