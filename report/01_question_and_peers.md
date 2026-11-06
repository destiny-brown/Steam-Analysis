# Question and peer momentum

## The question

On Sunday night, using only information that is already public, can we
forecast next week's peak Steam player count better than by assuming the
peak will not change?

We study 24 popular Steam games. For each game and each week, the model
predicts

```
log_growth = log(next week's peak) - log(this week's peak)
```

A week runs Monday 00:00 UTC to Sunday 23:59 UTC. Every input must be known
by the end of that Sunday.

## Why the comparison is the unchanged peak

Most games' weekly peaks move very little. A model that predicts
`log_growth = 0`, meaning next week's peak equals this week's, is therefore
already accurate most of the time, and it costs nothing. Any model worth
using has to beat it. We report each model's mean absolute error of log
growth divided by the unchanged-peak error: below 1 means the model added
something, at or above 1 means it did not.

This is also why training R² on raw player counts is not the headline. Raw
counts are dominated by which game is big, so R² looks high even for a
useless forecast, and extra features can raise training R² without helping
the weeks the model has not seen.

## Why the split is by time

A random 80/20 split would put later weeks of the same game in training and
earlier weeks in testing, so the model would learn from the future it is
asked to predict. Instead, every model trains on weeks ending through 4
October 2026, is tuned on 5–18 October, and is scored once on the
historical test weeks of 19 October–1 November. The live forecast for 9–15
November is saved on 8 November and not edited.

## Peer momentum

Players move with their genre: a big shooter release or a survival-game
trend can lift or drain similar games at the same time. To capture this,
each game is placed in one peer group a player would recognise
(`analysis/peers.csv`):

| Group | Games |
|---|---|
| Shooter | Counter-Strike 2, PUBG: BATTLEGROUNDS, Apex Legends, Team Fortress 2, Marvel Rivals, THE FINALS |
| Co-op / live service | Destiny 2, Warframe, HELLDIVERS 2, Left 4 Dead 2, Grand Theft Auto V |
| Survival / sandbox | Rust, Valheim, Palworld, Terraria, Stardew Valley |
| RPG | ELDEN RING, Baldur's Gate 3, Path of Exile, Lost Ark |
| Other PvP | Dota 2, Dead by Daylight, War Thunder, NARAKA: BLADEPOINT |

**Peer momentum** (`peer_median_growth`) is the median week-to-week log
growth of the *other* games in the group that week, leaving the game itself
out. It uses only that week and the week before, so it is known at the
Sunday cutoff. The median keeps one peer's launch or outage from dominating.
Grouping choices are explained in `analysis/peer_notes.md`.

## Peer result

*Not in yet: how often a game and its peer median move in the same
direction on training weeks.*

## Model comparison

*Not in yet: test error and error ratio, copied from
`model/results/test.csv`.*

*Not in yet: full XGBoost, without calendar, without peer column, copied
from `model/results/ablation.csv`.*

## Case

*Not in yet: from `analysis/case_peers.md`.*

## Live week

*Not in yet: filled on 16 November from `model/results/live_week.csv`.*

## Limits

About twelve usable weeks and 24 games. Daily samples before 6 October are
not the true hourly peak. Twitch is not in the model because it has no
history the model can train on; Steam news is the attention signal, and
SullyGnome was read by hand for at most one example. Momentum columns are
built from the same player series and are correlated. The study does not
show that a sale, a news post or a peer game caused a surge.
