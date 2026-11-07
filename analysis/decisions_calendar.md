# Calendar decisions

This file records the calendar decision made before each model score, as
required by the project workflow. The entries remain blank until Destiny
records the corresponding score.

1. Unchanged peak: validation MAE 0.08952672916666667, and this baseline does
   not use the calendar columns.
2. Weekday pattern: validation MAE 0.22546911146624907, and this model does
   not use the calendar columns.
3. Ridge: validation MAE 0.09803096891789091, and this model uses the sale and
   holiday calendar columns as features.
4. Shallow XGBoost: validation MAE 0.10912388828683117, and this model uses
   the sale and holiday calendar columns as features.
