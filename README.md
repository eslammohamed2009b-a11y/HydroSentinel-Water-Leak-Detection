# HydroSentinel AI

HydroSentinel AI is a school water-infrastructure decision-support system that detects likely leaks from telemetry and explains what to do next. It combines machine learning with contextual occupancy data (including Event Mode) to reduce false alarms and improve operational response.

## Key Capabilities

- Event-aware and normal-day leak detection workflows.
- Diagnostic outputs: predicted leak type, confidence, and estimated loss (L/min).
- Explainable recommendations for maintenance action.
- Built-in logging and feedback capture for iterative model improvement.

## System Architecture

HydroSentinel intentionally separates machine-learning logic from the user interface:

- `ml_engine.py`: ML/data core
	- Data validation and cleaning.
	- Training/persistence for diagnostic model bundles.
	- Event Mode-aware scoring and telemetry evaluation.
- `app.py`: Streamlit UI layer
	- User interactions (upload/demo mode, Event Mode toggle).
	- Visualization and decision-support cards.
	- Feedback and run logging.

This separation keeps the UI focused on interaction/reporting and keeps model logic testable and reusable.

## Data Inputs

Expected telemetry columns:

- `Timestamp`
- `Flow_Rate_LPM`
- `Avg_Pressure_PSI`
- `Occupancy_Status`

Bundled sample files now follow an explicit scenario matrix:

- `normal.csv`: baseline school day (no leak)
- `normal_leak.csv`: normal school day with leak injection
- `event.csv`: event day without leak
- `event_leak.csv`: event day with leak

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Launch the Streamlit app:

```bash
streamlit run app.py
```

3. In the sidebar:
- Choose upload mode or simulated live demo.
- Toggle Event Mode ON during school events for event-aware training/scoring.

## Tests

Run basic system tests:

```bash
python -m unittest test_system.py
```

## License

See `LICENSE`.
