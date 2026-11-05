# Calendar decisions

This file records the calendar decision made before each model score, as
required by the project workflow. The entries remain blank until Destiny
records the corresponding score.

1. Unchanged peak: validation MAE 0.0895. The unchanged-peak baseline does
   not use the calendar columns.
2. Weekday pattern: validation MAE 0.2255. The weekday-pattern model does not
   use the calendar columns.
3. Ridge: validation MAE 0.0955. Ridge uses the sale and holiday calendar
   columns as features.
4. Shallow XGBoost: validation MAE 0.1099. Removing the calendar columns
   worsened XGBoost validation MAE to 0.1141.
