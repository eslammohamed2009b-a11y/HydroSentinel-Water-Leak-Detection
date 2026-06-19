import pandas as pd
import numpy as np

# Generate a US academic school-year dataset spanning August 1, 2026 to July 31, 2027.
# Weekdays are higher-flow school days; weekends and breaks are lower-flow periods.

DATES = pd.date_range(start='2026-08-01', end='2027-07-31', freq='D')

WINTER_BREAK = pd.date_range(start='2026-12-20', end='2027-01-05', freq='D')
SPRING_BREAK = pd.date_range(start='2027-04-03', end='2027-04-09', freq='D')
SUMMER_BREAK_START = pd.Timestamp('2027-06-15')


def is_school_day(date: pd.Timestamp) -> bool:
    if date.weekday() >= 5:
        return False
    if date in WINTER_BREAK or date in SPRING_BREAK or date >= SUMMER_BREAK_START:
        return False
    return True


def occupancy_status(date: pd.Timestamp) -> str:
    return 'Class_Hours' if is_school_day(date) else 'After_Hours'


def baseline_usage(date: pd.Timestamp) -> tuple[float, float]:
    if is_school_day(date):
        flow = np.random.normal(17.4, 1.3)
        pressure = np.random.normal(51.2, 1.1)
    else:
        flow = np.random.normal(4.2, 1.0)
        pressure = np.random.normal(42.0, 1.5)

    flow = float(np.clip(flow, 2.0, 26.0))
    pressure = float(np.clip(pressure, 35.0, 55.0))
    return round(flow, 1), round(pressure, 1)


def create_data(mode: str) -> pd.DataFrame:
    rows = []
    for date in DATES:
        flow, pressure = baseline_usage(date)
        status = occupancy_status(date)

        if mode != 'no_leak':
            leak_day = pd.Timestamp('2027-04-12')
            if date == leak_day:
                if mode == 'leak_normal':
                    flow = float(np.clip(np.random.normal(48.0, 3.5), 35.0, 65.0))
                    pressure = float(np.clip(np.random.normal(36.0, 1.8), 28.0, 42.0))
                else:
                    flow = float(np.clip(np.random.normal(73.0, 4.0), 55.0, 90.0))
                    pressure = float(np.clip(np.random.normal(31.0, 2.2), 24.0, 38.0))

        rows.append([date, flow, pressure, status])

    return pd.DataFrame(rows, columns=['Timestamp', 'Flow_Rate_LPM', 'Avg_Pressure_PSI', 'Occupancy_Status'])


if __name__ == '__main__':
    create_data('no_leak').to_csv('no_leak.csv', index=False)
    create_data('leak_normal').to_csv('leak_normal.csv', index=False)
    create_data('leak_event').to_csv('leak_event.csv', index=False)

    print('Generated updated school-year datasets for HydroSentinel.')
