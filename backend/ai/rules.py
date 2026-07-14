"""Contextual logic for HydroSentinel.

Provides rule-based checks to supplement anomaly detection models.
"""

from typing import Dict

import pandas as pd


def evaluate_row(row: pd.Series) -> Dict[str, bool]:
    """Evaluate a single reading against contextual rules."""
    flow = float(row["Flow_Rate_LPM"])
    status = str(row["Occupancy_Status"])

    normal = True
    leak_alert = False

    if status == "Class_Hours":
        normal = 10.0 <= flow <= 20.0
    elif status in ("After_Hours", "Vacation"):
        normal = 0.0 <= flow <= 5.0
        if flow > 8.0:
            leak_alert = True
    else:
        normal = 0.0 <= flow <= 5.0
        if flow > 8.0:
            leak_alert = True

    return {"Rule_Normal": normal, "Rule_Leak_Alert": leak_alert}


def evaluate_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply evaluate_row across a DataFrame and return an annotated copy."""
    out = df.copy()
    annotations = out.apply(lambda row: pd.Series(evaluate_row(row)), axis=1)
    return pd.concat([out, annotations], axis=1)