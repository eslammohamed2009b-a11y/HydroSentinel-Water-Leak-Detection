"""Contextual logic for HydroSentinel
Provides rule-based checks to supplement anomaly detection models.

Rules implemented:
1. If `Occupancy_Status` == 'Class_Hours' => normal flow between 10 and 20 LPM.
2. If `Occupancy_Status` == 'After_Hours' or 'Vacation' => normal flow between 0 and 5 LPM.
3. Leak alert during `After_Hours`/`Vacation` only if flow > 8 LPM.

Functions:
- evaluate_row(row) -> dict: evaluates a single row
- evaluate_df(df) -> df: returns a copy with `Rule_Normal` and `Rule_Leak_Alert` columns
"""
import pandas as pd
from typing import Dict


def evaluate_row(row: pd.Series) -> Dict[str, bool]:
    """Evaluate a single reading against contextual rules.

    Returns a dict with keys:
      - 'Rule_Normal': True if the reading falls inside the expected range
      - 'Rule_Leak_Alert': True if a leak should be signalled by rules
    """
    flow = float(row['Flow_Rate_LPM'])
    status = str(row['Occupancy_Status'])

    # default
    normal = True
    leak_alert = False

    if status == 'Class_Hours':
        normal = (10.0 <= flow <= 20.0)
    elif status in ('After_Hours', 'Vacation'):
        normal = (0.0 <= flow <= 5.0)
        if flow > 8.0:
            leak_alert = True
    else:
        # conservative fallback: treat unknown as After_Hours
        normal = (0.0 <= flow <= 5.0)
        if flow > 8.0:
            leak_alert = True

    return {'Rule_Normal': normal, 'Rule_Leak_Alert': leak_alert}


def evaluate_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply `evaluate_row` across a DataFrame and return an annotated copy."""
    out = df.copy()
    anns = out.apply(lambda r: pd.Series(evaluate_row(r)), axis=1)
    out = pd.concat([out, anns], axis=1)
    return out
