# Peer decisions

One sentence about the peer column after each model score, copied from
`model/results/validation.csv` and `model/results/ablation.csv`.

1. Unchanged peak: validation MAE 0.0895. The unchanged-peak baseline
   predicts zero growth and does not use `peer_median_growth`.
2. Weekday pattern: validation MAE 0.2255. The weekday-pattern model repeats
   each game's own recent days and does not use `peer_median_growth`.
3. Ridge: validation MAE 0.0955. Ridge uses momentum and calendar columns
   only, so `peer_median_growth` is not one of its inputs.
4. Shallow XGBoost: validation MAE 0.1099. Removing `peer_median_growth` left
   the validation MAE unchanged at 0.1099, because in this run the column was
   empty in all 312 rows of `week_panel.csv` (`peer_set_size` is 0
   everywhere), so the peer feature has not yet been tested.
