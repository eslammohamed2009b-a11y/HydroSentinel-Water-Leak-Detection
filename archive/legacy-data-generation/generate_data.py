import pandas as pd
import numpy as np

# Generate a school water usage dataset for 2026.
# Summer break: June 15 - August 15, Winter break: Dec 20 - Jan 5.
# School days have normal school flow, breaks have near-zero baseline.

dates = pd.date_range(start='2026-01-01', end='2026-12-31', freq='D')


def is_school_break(date: pd.Timestamp) -> bool:
    if (date.month == 6 and date.day >= 15) or (date.month == 7) or (date.month == 8 and date.day <= 15):
        return True
    if (date.month == 12 and date.day >= 20) or (date.month == 1 and date.day <= 5):
        return True
    return False


def baseline_usage(date: pd.Timestamp) -> tuple[float, float, str]:
    if is_school_break(date):
        flow = np.random.uniform(0.5, 2.0)
        pressure = 45.0 + np.random.normal(0, 1.0)
        status = 'After_Hours'
    elif date.weekday() < 5:
        flow = np.random.uniform(14.0, 16.0)
        pressure = 50.0 + np.random.normal(0, 0.5)
        status = 'Class_Hours'
    else:
        flow = np.random.uniform(4.0, 7.0)
        pressure = 48.0 + np.random.normal(0, 1.0)
        status = 'After_Hours'

    return round(float(flow), 1), round(float(pressure), 1), status


def create_data(mode: str) -> pd.DataFrame:
    rows = []
    leak_day = pd.Timestamp('2026-04-13')
    for date in dates:
        flow, pressure, status = baseline_usage(date)

        if mode in ('leak_normal', 'leak_event') and date == leak_day:
            flow = float(np.clip(np.random.normal(45.0, 3.0), 35.0, 60.0))
            pressure = float(np.clip(np.random.normal(35.0, 1.2), 28.0, 42.0))
            status = 'Class_Hours'
            if mode == 'leak_event':
                flow = float(np.clip(flow + 20.0, 55.0, 85.0))
                pressure = float(np.clip(pressure - 5.0, 24.0, 38.0))

        rows.append([date, flow, pressure, status])

    return pd.DataFrame(rows, columns=['Timestamp', 'Flow_Rate_LPM', 'Avg_Pressure_PSI', 'Occupancy_Status'])


if __name__ == '__main__':
    create_data('no_leak').to_csv('no_leak.csv', index=False)
    create_data('leak_normal').to_csv('leak_normal.csv', index=False)
    create_data('leak_event').to_csv('leak_event.csv', index=False)
    print('Generated updated school-seasonality dataset files.')