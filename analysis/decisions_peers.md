# Peer decisions

One sentence about the peer column after each model score. Scores are
copied from `model/results/validation.csv` and `model/results/ablation.csv`
as of 7 November 2026 (panel rebuilt with `analysis/peers.csv` in commit
a1cdfe2).

1. Unchanged peak: validation MAE 0.0895. The unchanged-peak baseline
   predicts zero growth and does not use `peer_median_growth`.
2. Weekday pattern: validation MAE 0.2255. The weekday-pattern model repeats
   each game's own recent days and does not use `peer_median_growth`.
3. Ridge: validation MAE 0.0980. `model/train.py` fits Ridge on the full
   feature list, so Ridge already includes `peer_median_growth`, although the
   README ladder adds the peer column only at the XGBoost step.
4. Shallow XGBoost: validation MAE 0.1091. Removing `peer_median_growth`
   raised the validation MAE to 0.1099, a change of 0.0008, so the peer
   column made almost no difference and neither version beat the unchanged
   peak.
