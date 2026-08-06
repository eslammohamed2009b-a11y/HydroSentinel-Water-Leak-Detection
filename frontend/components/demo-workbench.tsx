"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { TelemetryChart, type TelemetryPoint } from "@/components/telemetry-chart";
import { fetchScenarios, runAnalysis, type AnalysisResponse, type ScenarioSummary } from "@/services/analysis";

type DemoScenario = {
  key: "normal" | "hidden-leak" | "high-activity" | "high-activity-leak";
  title: string;
  description: string;
  eventMode: boolean;
  hasLeak: boolean;
};

const demoScenarios: DemoScenario[] = [
  { key: "normal", title: "Normal Operation", description: "Expected building demand", eventMode: false, hasLeak: false },
  { key: "hidden-leak", title: "Hidden Leak", description: "Abnormal flow and pressure behavior", eventMode: false, hasLeak: true },
  { key: "high-activity", title: "High Activity", description: "Legitimate high demand", eventMode: true, hasLeak: false },
  { key: "high-activity-leak", title: "High Activity + Leak", description: "Context plus abnormal behavior", eventMode: true, hasLeak: true },
];

function scenarioFor(items: ScenarioSummary[], target: Pick<DemoScenario, "eventMode" | "hasLeak">) {
  return items.find((item) => item.occupancy_mode === (target.eventMode ? "event" : "normal") && item.expected_has_leak === target.hasLeak);
}

function asNumber(value: unknown) {
  return typeof value === "number" ? value : Number(value ?? 0);
}

function evidenceValue(value: unknown, suffix: string) {
  return typeof value === "number" ? `${value > 0 ? "+" : ""}${value.toFixed(1)}${suffix}` : "—";
}

function pressureDropValue(value: unknown) {
  return typeof value === "number" ? `${Math.max(value, 0).toFixed(1)}% drop` : "—";
}

function HelperPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <details className="border border-[var(--line)] bg-[var(--surface-strong)] px-3 py-2 text-sm">
      <summary className="cursor-pointer font-medium text-[var(--foreground)]">{title}</summary>
      <p className="mt-2 leading-6 text-[var(--muted)]">{children}</p>
    </details>
  );
}

export function DemoWorkbench() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedKey, setSelectedKey] = useState<DemoScenario["key"]>("hidden-leak");
  const [eventMode, setEventMode] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guidedMode, setGuidedMode] = useState(true);

  const selected = demoScenarios.find((scenario) => scenario.key === selectedKey) ?? demoScenarios[0];
  const selectedScenario = scenarioFor(scenarios, { eventMode, hasLeak: selected.hasLeak });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const items = await fetchScenarios();
        if (!cancelled) {
          setScenarios(items);
          const initial = scenarioFor(items, { eventMode: false, hasLeak: true });
          if (!initial) setError("The demo scenarios are unavailable. Please retry.");
        }
      } catch {
        if (!cancelled) setError("Could not connect to the analysis service. Please retry.");
      } finally {
        if (!cancelled) setConnecting(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  function selectScenario(next: DemoScenario) {
    setSelectedKey(next.key);
    setEventMode(next.eventMode);
    setError(null);
  }

  function selectContext(nextEventMode: boolean) {
    const matching = demoScenarios.find((scenario) => scenario.eventMode === nextEventMode && scenario.hasLeak === selected.hasLeak);
    if (matching) setSelectedKey(matching.key);
    setEventMode(nextEventMode);
    setError(null);
  }

  async function handleAnalyze() {
    if (loading || connecting || !selectedScenario) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await runAnalysis({ scenario_selected: selectedScenario.filename, event_mode: eventMode }));
    } catch {
      setError("Analysis could not be completed. Please retry in a moment.");
    } finally {
      setLoading(false);
    }
  }

  const telemetry = useDeferredValue(result?.telemetry_points ?? []);
  const points = useMemo<TelemetryPoint[]>(() => telemetry.map((point) => ({
    Timestamp: String(point.Timestamp ?? ""),
    Flow_Rate_LPM: asNumber(point.Flow_Rate_LPM),
    Avg_Pressure_PSI: asNumber(point.Avg_Pressure_PSI),
    Leak_Flag: Boolean(point.Leak_Flag),
  })), [telemetry]);
  const reasoning = result?.insights.reasoning as Record<string, unknown> | undefined;
  const financial = result?.financial_loss ?? {};
  const environmental = result?.environmental_impact ?? {};

  return (
    <DashboardShell title="Analyze">
      <div className="grid gap-6">
        <section className="border-b border-[var(--line)] pb-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">HydroSentinel AI</div>
              <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">Context-aware water anomaly detection for managed facilities.</h1>
              {guidedMode ? <p className="mt-2 text-sm text-[var(--muted)]">Choose a synthetic/simulated scenario, set operating context, then review the resulting evidence with a human decision-maker.</p> : null}
            </div>
            <div className="inline-flex border border-[var(--line)] p-1 text-sm">
              <button aria-pressed={guidedMode} className={`px-3 py-2 font-medium ${guidedMode ? "bg-[var(--primary)] text-white" : "text-[var(--muted)] hover:bg-[var(--surface-strong)]"}`} onClick={() => setGuidedMode(true)} type="button">Guided Mode</button>
              <button aria-pressed={!guidedMode} className={`px-3 py-2 font-medium ${!guidedMode ? "bg-[var(--primary)] text-white" : "text-[var(--muted)] hover:bg-[var(--surface-strong)]"}`} onClick={() => setGuidedMode(false)} type="button">Expert Mode</button>
            </div>
          </div>
        </section>

        <section className="border border-[var(--line)] bg-white p-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Choose a scenario</div>
              {guidedMode ? <p className="mt-1 text-sm text-[var(--muted)]">Compare normal demand, abnormal behavior, and legitimate high activity using the existing seeded scenarios.</p> : null}
            </div>
            {connecting ? <span className="text-sm text-[var(--muted)]">Connecting to analysis service…</span> : null}
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {demoScenarios.map((scenario) => {
              const available = Boolean(scenarioFor(scenarios, scenario));
              const active = scenario.key === selectedKey;
              return (
                <button
                  key={scenario.key}
                  aria-pressed={active}
                  className={`border p-4 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-50 ${active ? "border-[var(--primary)] bg-[rgba(15,92,69,0.06)]" : "border-[var(--line)] bg-white hover:border-[var(--primary)]"}`}
                  disabled={connecting || loading || !available}
                  onClick={() => selectScenario(scenario)}
                  type="button"
                >
                  <div className="text-sm font-semibold">{scenario.title}</div>
                  <div className="mt-1 text-xs leading-5 text-[var(--muted)]">{scenario.description}</div>
                </button>
              );
            })}
          </div>
          {guidedMode ? <div className="mt-3"><HelperPanel title="Why these scenarios?">They provide a controlled comparison of normal operation, suspicious flow/pressure behavior, legitimate high demand, and high demand with a flagged pattern. They are seeded synthetic/simulated scenarios, not live building telemetry.</HelperPanel></div> : null}

          <div className="mt-5 border-t border-[var(--line)] pt-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Operating context</div>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <div className="inline-flex border border-[var(--line)] p-1">
                <button aria-pressed={!eventMode} className={`px-3 py-2 text-sm font-medium ${!eventMode ? "bg-[var(--primary)] text-white" : "text-[var(--muted)] hover:bg-[var(--surface-strong)]"}`} disabled={connecting || loading} onClick={() => selectContext(false)} type="button">Standard</button>
                <button aria-pressed={eventMode} className={`px-3 py-2 text-sm font-medium ${eventMode ? "bg-[var(--primary)] text-white" : "text-[var(--muted)] hover:bg-[var(--surface-strong)]"}`} disabled={connecting || loading} onClick={() => selectContext(true)} type="button">Event / High Activity</button>
              </div>
              {guidedMode ? <p className="max-w-xl text-sm text-[var(--muted)]">Operating context helps distinguish legitimate high-demand periods from suspicious behavior.</p> : null}
            </div>
            {guidedMode ? <div className="mt-3"><HelperPanel title="Why does operating context matter?">A higher flow rate during an event can be expected. The model evaluates flow and pressure alongside the selected operating context rather than treating high demand alone as a leak.</HelperPanel></div> : null}
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-4">
            <button className="bg-[var(--primary)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[var(--primary-strong)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-60" disabled={connecting || loading || !selectedScenario} onClick={() => void handleAnalyze()} type="button">
              {loading ? "Analyzing telemetry…" : "Analyze scenario"}
            </button>
            {guidedMode ? <p className="text-sm text-[var(--muted)]">High demand alone is not sufficient evidence of a leak; operating context changes interpretation.</p> : null}
          </div>
          {guidedMode ? <div className="mt-3"><HelperPanel title="What happens when I click Analyze?">HydroSentinel evaluates the selected flow, pressure, and operating-context telemetry against the learned synthetic baseline, then saves the result to your private history for review.</HelperPanel></div> : null}
          {error ? <p className="mt-4 border-l-2 border-[var(--danger)] bg-[rgba(195,63,56,0.08)] px-3 py-2 text-sm text-[var(--danger)]">{error}</p> : null}
        </section>

        <section aria-live="polite" className={`border p-5 ${result?.has_leak ? "border-[rgba(195,63,56,0.45)] bg-[rgba(195,63,56,0.04)]" : result ? "border-[rgba(49,120,87,0.45)] bg-[rgba(49,120,87,0.04)]" : "border-[var(--line)] bg-white"}`}>
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div>
              <div className={`text-xs font-semibold uppercase tracking-[0.22em] ${result?.has_leak ? "text-[var(--danger)]" : "text-[var(--primary)]"}`}>Analysis status</div>
              <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em]">{result ? (result.has_leak ? "Review required" : "No anomaly detected") : "Awaiting analysis"}</h2>
              {guidedMode ? <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted)]">{result?.reasoning_string ?? "Choose a scenario to compare normal demand, suspected leak behavior, and legitimate high-activity demand."}</p> : null}
            </div>
            <div className="min-w-36 border-l border-[var(--line)] pl-5">
              <div className="text-xs uppercase tracking-wider text-[var(--muted)]">Model score</div>
              <div className="mt-1 text-3xl font-semibold">{result ? `${result.confidence.toFixed(1)}%` : "—"}</div>
              {guidedMode ? <div className="mt-1 text-xs text-[var(--muted)]">Not a calibrated probability</div> : null}
            </div>
          </div>
          <dl className="mt-5 grid gap-4 border-t border-[var(--line)] pt-5 sm:grid-cols-3">
            <div><dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Estimated loss rate</dt><dd className="mt-1 text-lg font-semibold">{result ? `${result.leak_lpm.toFixed(1)} L/min` : "—"}</dd></div>
            <div><dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Operating context</dt><dd className="mt-1 text-lg font-semibold">{result ? (result.event_mode ? "Event / High Activity" : "Standard") : "—"}</dd></div>
            <div><dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Pattern label</dt><dd className="mt-1 text-lg font-semibold">{result?.leak_type?.replaceAll("_", " ") ?? "—"}</dd></div>
          </dl>
          {guidedMode ? <div className="mt-4"><HelperPanel title="What does model score mean?">It is the classifier score for the detected pattern in this synthetic/simulated scenario. It is not a calibrated probability or a confirmation that a physical leak exists.</HelperPanel></div> : null}
        </section>

        {result ? (
          <>
            <section className="border border-[var(--line)] bg-white p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">AI reasoning</div>
              {result.has_leak ? (
                <ol className="mt-4 grid gap-2 text-sm leading-6 text-[var(--foreground)]">
                  <li><span className="font-semibold">1. Flow evidence:</span> {typeof reasoning?.current_flow === "number" && typeof reasoning?.baseline_flow === "number" ? `${reasoning.current_flow.toFixed(1)} L/min observed against a ${reasoning.baseline_flow.toFixed(1)} L/min learned baseline.` : "Flow was evaluated against the learned synthetic baseline."}</li>
                  <li><span className="font-semibold">2. Pressure evidence:</span> {typeof reasoning?.current_pressure === "number" && typeof reasoning?.baseline_pressure === "number" ? `${reasoning.current_pressure.toFixed(1)} PSI observed against a ${reasoning.baseline_pressure.toFixed(1)} PSI learned baseline${typeof reasoning.pressure_drop_pct === "number" ? ` (${pressureDropValue(reasoning.pressure_drop_pct)})` : ""}.` : "Pressure was evaluated against the learned synthetic baseline."}</li>
                  <li><span className="font-semibold">3. Operating context:</span> compared as {result.event_mode ? "Event / High Activity" : "Standard"}.</li>
                  <li><span className="font-semibold">4. Interpretation:</span> the pattern differs from the learned synthetic baseline.</li>
                  <li><span className="font-semibold">5. Decision support:</span> human review required.</li>
                </ol>
              ) : (
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">Flow, pressure, and operating context remained within the learned synthetic baseline → no review required for this simulated scenario.</p>
              )}
            </section>
            <TelemetryChart points={points} />
            {guidedMode ? <HelperPanel title="How do I read the flow and pressure charts?">The charts use separate labeled scales because flow rate and pressure are different measurements. The line shows each telemetry signal over time; red markers identify samples the backend flagged for review.</HelperPanel> : null}
            <div className="grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
              <section className="border border-[var(--line)] bg-white p-5">
                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Evidence</div>
                {result.has_leak && reasoning ? (
                  <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <div><div className="text-xs text-[var(--muted)]">Flow change</div><div className="mt-1 text-lg font-semibold">{evidenceValue(reasoning.flow_delta_pct, "%")}</div></div>
                    <div><div className="text-xs text-[var(--muted)]">Pressure drop</div><div className="mt-1 text-lg font-semibold">{pressureDropValue(reasoning.pressure_drop_pct)}</div></div>
                    <div><div className="text-xs text-[var(--muted)]">Current flow</div><div className="mt-1 text-lg font-semibold">{asNumber(reasoning.current_flow).toFixed(1)} L/min</div></div>
                    <div><div className="text-xs text-[var(--muted)]">Current pressure</div><div className="mt-1 text-lg font-semibold">{asNumber(reasoning.current_pressure).toFixed(1)} PSI</div></div>
                  </div>
                ) : <p className="mt-3 text-sm leading-6 text-[var(--muted)]">No anomaly evidence was surfaced for this synthetic/simulated scenario.</p>}
                {typeof reasoning?.narrative === "string" ? <p className="mt-4 text-sm leading-6 text-[var(--muted)]">{reasoning.narrative}</p> : null}
              </section>
              <section className="border border-[var(--line)] bg-white p-5">
                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Estimated impact</div>
                <div className="mt-4 text-sm"><div className="text-[var(--muted)]">Financial</div><div className="mt-1 text-xl font-semibold">{String(financial.current_loss_label ?? "$0.00/hour")}</div></div>
                <div className="mt-4 text-sm"><div className="text-[var(--muted)]">Sampled water impact</div><div className="mt-1 text-xl font-semibold">{asNumber(environmental.liters_saved).toFixed(1)} L</div></div>
                <p className="mt-4 text-xs leading-5 text-[var(--muted)]">{String(financial.narrative ?? environmental.narrative ?? "Estimated impacts are available after analysis.")}</p>
                {guidedMode ? <div className="mt-4"><HelperPanel title="How are impact estimates calculated?">They are existing model estimates derived from the estimated loss rate and stated cost and water-treatment assumptions. They are not measured savings or a guarantee of impact.</HelperPanel></div> : null}
              </section>
            </div>
          </>
        ) : null}

        <section className="border-l-2 border-[var(--primary)] bg-[var(--surface-strong)] p-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">System transparency</div>
          <ul className="mt-3 grid gap-2 text-sm leading-6 text-[var(--muted)] sm:grid-cols-2">
            <li>Data source: seeded synthetic/simulated scenarios.</li>
            <li>Inputs: flow, pressure, and operating context.</li>
            <li>Model score is not a calibrated probability.</li>
            <li>Estimated loss is a model estimate.</li>
            <li>Not physically deployed or validated on building infrastructure.</li>
            <li>Human review is required.</li>
          </ul>
          {guidedMode ? <div className="mt-3"><HelperPanel title="What can and can’t the system conclude?">It can surface patterns that differ from its learned synthetic baseline and provide decision-support estimates. It cannot confirm a physical leak, replace site inspection, or guarantee outcomes.</HelperPanel></div> : null}
        </section>
      </div>
    </DashboardShell>
  );
}
