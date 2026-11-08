# Calendar decisions

1. Unchanged peak: validation MAE 0.08952672916666667, and this baseline
   evaluated no calendar columns.
2. Weekday pattern: validation MAE 0.22546911146624907, and this model
   evaluated no calendar columns.
3. Ridge: validation MAE 0.09803096891789091, and this model utilized the sale
   and holiday calendar columns as features.
4. Shallow XGBoost: validation MAE 0.10912388828683117, and this model
   utilized the sale and holiday calendar columns as features.
