"use client";

import { startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { KpiCard } from "@/components/kpi-card";
import { TelemetryChart } from "@/components/telemetry-chart";
import { fetchScenarios, runAnalysis, type AnalysisResponse, type ScenarioSummary } from "@/services/analysis";

type Variant = "operational" | "executive";

type AnalysisWorkbenchProps = {
  variant: Variant;
};

export function AnalysisWorkbench({ variant }: AnalysisWorkbenchProps) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("normal.csv");
  const [eventMode, setEventMode] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    startTransition(async () => {
      try {
        const items = await fetchScenarios();
        setScenarios(items);
        if (items.length > 0) {
          setSelectedScenario(items[0].filename);
        }
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : "Could not load scenarios.";
        setError(message);
      }
    });
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const analysis = await runAnalysis({ scenario_selected: selectedScenario, event_mode: eventMode });
      setResult(analysis);
    } catch (analysisError) {
      const message = analysisError instanceof Error ? analysisError.message : "Analysis failed.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const deferredTelemetry = useDeferredValue(result?.telemetry_points ?? []);
  const telemetryPoints = useMemo(
    () =>
      deferredTelemetry.map((point) => ({
        Timestamp: String(point.Timestamp ?? ""),
        Flow_Rate_LPM: Number(point.Flow_Rate_LPM ?? 0),
        Leak_Flag: Boolean(point.Leak_Flag ?? false),
      })),
    [deferredTelemetry],
  );

  const financial = (result?.financial_loss ?? {}) as Record<string, unknown>;
  const environmental = (result?.environmental_impact ?? {}) as Record<string, unknown>;
  const headline =
    variant === "operational"
      ? {
          title: "Operations View",
          eyebrow: "Field response dashboard",
          subtitle: "Run the migrated analysis workflow and inspect anomaly evidence with operator-oriented controls.",
        }
      : {
          title: "Executive View",
          eyebrow: "Leadership water risk overview",
          subtitle: "Use the same backend result but frame it for financial exposure, governance, and sustainability decisions.",
        };

  const aside = (
    <div className="grid gap-5">
      <section className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
        <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Analysis Controls</div>
        <div className="mt-4 grid gap-4">
          <label className="grid gap-2 text-sm text-[var(--muted)]">
            Scenario
            <select className="rounded-2xl border border-[var(--line)] bg-white px-4 py-3" value={selectedScenario} onChange={(event) => setSelectedScenario(event.target.value)}>
              {scenarios.map((scenario) => (
                <option key={scenario.slug} value={scenario.filename}>
                  {scenario.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center justify-between rounded-2xl border border-[var(--line)] bg-[var(--surface-strong)] px-4 py-3 text-sm text-[var(--foreground)]">
            <span>Event Mode</span>
            <input checked={eventMode} onChange={(event) => setEventMode(event.target.checked)} type="checkbox" />
          </label>
          <button className="rounded-2xl bg-[var(--primary)] px-4 py-3 font-semibold text-white transition hover:bg-[var(--primary-strong)] disabled:opacity-60" disabled={loading} onClick={handleAnalyze} type="button">
            {loading ? "Running analysis..." : "Analyze"}
          </button>
        </div>
      </section>
      <section className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
        <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Reasoning</div>
        <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{result?.reasoning_string ?? "Run an analysis to view the backend reasoning string."}</p>
      </section>
      {error ? <p className="rounded-[1.6rem] bg-[rgba(195,63,56,0.1)] p-4 text-sm text-[var(--danger)]">{error}</p> : null}
    </div>
  );

  return (
    <DashboardShell aside={aside} eyebrow={headline.eyebrow} subtitle={headline.subtitle} title={headline.title}>
      <div className="grid gap-5">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KpiCard label="System Status" note={result?.has_leak ? "Leak signature detected by the migrated backend." : "No leak has been detected in the active analysis."} tone={result?.has_leak ? "danger" : "success"} value={result ? (result.has_leak ? "Leak" : "Stable") : "Idle"} />
          <KpiCard label="Leak Type" note="Classifier output returned by FastAPI." tone="accent" value={result?.leak_type?.replaceAll("_", " ") ?? "None"} />
          <KpiCard label="Water Loss" note="Predicted leak loss rate in liters per minute." value={result ? `${result.leak_lpm.toFixed(1)} L/m` : "0.0 L/m"} />
          <KpiCard label="Confidence" note="Top leak confidence for the active analysis." value={result ? `${result.confidence.toFixed(1)}%` : "0.0%"} />
        </div>
        <TelemetryChart points={telemetryPoints} />
        <div className="grid gap-5 lg:grid-cols-2">
          <section className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
            <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Financial impact</div>
            <div className="mt-4 text-3xl font-semibold tracking-[-0.04em]">{String(financial.current_loss_label ?? "$0.00/hour")}</div>
            <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{String(financial.narrative ?? "No active financial impact narrative.")}</p>
          </section>
          <section className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
            <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Environmental impact</div>
            <div className="mt-4 text-3xl font-semibold tracking-[-0.04em]">{`${Number(environmental.liters_saved ?? 0).toFixed(1)} L`}</div>
            <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{String(environmental.narrative ?? "No environmental narrative available yet.")}</p>
          </section>
        </div>
        {variant === "executive" ? (
          <section className="rounded-[1.6rem] border border-[var(--line)] bg-[linear-gradient(135deg,rgba(15,92,69,0.98),rgba(11,67,50,0.94))] p-6 text-white">
            <div className="text-xs uppercase tracking-[0.28em] text-white/70">Executive framing</div>
            <h3 className="mt-3 text-3xl font-semibold tracking-[-0.05em]">Decision-ready summary</h3>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-white/78">The executive page reuses the same backend result but shifts emphasis toward financial exposure, environmental cost, and governance-safe interpretation rather than raw anomaly detail.</p>
          </section>
        ) : null}
      </div>
    </DashboardShell>
  );
}