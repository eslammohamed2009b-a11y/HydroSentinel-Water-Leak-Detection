"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { TelemetryChart } from "@/components/telemetry-chart";
import { fetchScenarios, runAnalysis, type AnalysisResponse, type ScenarioSummary } from "@/services/analysis";

type Variant = "operational" | "executive";

export function AnalysisWorkbench({ variant }: { variant: Variant }) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("normal.csv");
  const [eventMode, setEventMode] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const items = await fetchScenarios();
        if (!cancelled) { setScenarios(items); if (items[0]) setSelectedScenario(items[0].filename); }
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Could not connect to the analysis service. Please retry.");
      } finally { if (!cancelled) setConnecting(false); }
    }
    void load(); return () => { cancelled = true; };
  }, []);

  async function handleAnalyze() {
    if (loading || connecting) return;
    setLoading(true); setError(null);
    try { setResult(await runAnalysis({ scenario_selected: selectedScenario, event_mode: eventMode })); }
    catch (analysisError) { setError(analysisError instanceof Error ? analysisError.message : "Analysis failed. Please try again."); }
    finally { setLoading(false); }
  }

  const deferred = useDeferredValue(result?.telemetry_points ?? []);
  const telemetry = useMemo(() => deferred.map((point) => ({ Timestamp: String(point.Timestamp ?? ""), Flow_Rate_LPM: Number(point.Flow_Rate_LPM ?? 0), Avg_Pressure_PSI: Number(point.Avg_Pressure_PSI ?? 0), Leak_Flag: Boolean(point.Leak_Flag) })), [deferred]);
  const financial = result?.financial_loss ?? {}, environmental = result?.environmental_impact ?? {};
  return <DashboardShell title={variant === "executive" ? "Water Risk Summary" : "Water Anomaly Analysis"}>
    <div className="grid gap-6">
      <section className="border border-[var(--line)] bg-white p-5"><div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-end"><label className="grid gap-2 text-sm font-medium">Scenario<select className="border border-[var(--line)] bg-white px-3 py-2 text-sm disabled:bg-[var(--surface-strong)]" disabled={connecting || loading} value={selectedScenario} onChange={(event) => setSelectedScenario(event.target.value)}>{scenarios.map((scenario) => <option key={scenario.slug} value={scenario.filename}>{scenario.label}</option>)}</select></label><label className="flex items-center gap-2 pb-2 text-sm"><input checked={eventMode} disabled={connecting || loading} onChange={(event) => setEventMode(event.target.checked)} type="checkbox" />Building Operating Context: Event / High Activity</label><button className="bg-[var(--primary)] px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60" disabled={connecting || loading || !scenarios.length} onClick={handleAnalyze} type="button">{loading ? "Analyzing…" : "Analyze"}</button></div>{connecting ? <p className="mt-4 text-sm text-[var(--muted)]">Connecting to analysis service…</p> : null}{error ? <p className="mt-4 bg-[rgba(195,63,56,0.08)] p-3 text-sm text-[var(--danger)]">{error}</p> : null}</section>
      <section className="border border-[var(--line)] bg-white p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">Screening result</div><h2 className={`mt-1 text-2xl font-semibold ${result?.has_leak ? "text-[var(--danger)]" : "text-[var(--primary)]"}`}>{result ? (result.has_leak ? "Review required" : "No anomaly detected") : "Awaiting analysis"}</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">{result?.reasoning_string ?? "Choose a scenario and run analysis to inspect flow, pressure, and operating-context signals."}</p></div><div className="text-right text-sm"><div className="text-[var(--muted)]">Model score</div><div className="text-xl font-semibold">{result ? `${result.confidence.toFixed(1)}%` : "—"}</div></div></div><div className="mt-5 grid gap-4 border-t border-[var(--line)] pt-4 sm:grid-cols-2 lg:grid-cols-3"><div><div className="text-xs text-[var(--muted)]">Estimated loss rate</div><div className="mt-1 font-semibold">{result ? `${result.leak_lpm.toFixed(1)} L/min` : "—"}</div></div><div><div className="text-xs text-[var(--muted)]">Operating context</div><div className="mt-1 font-semibold">{result?.event_mode ? "Event / High Activity" : "Standard"}</div></div><div><div className="text-xs text-[var(--muted)]">Pattern label</div><div className="mt-1 font-semibold">{result?.leak_type?.replaceAll("_", " ") ?? "—"}</div></div></div></section>
      <TelemetryChart points={telemetry} />
      <div className="grid gap-4 md:grid-cols-2"><section className="border border-[var(--line)] bg-white p-5"><div className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">Estimated financial impact</div><div className="mt-2 text-xl font-semibold">{String(financial.current_loss_label ?? "$0.00/hour")}</div><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{String(financial.narrative ?? "Available after analysis.")}</p></section><section className="border border-[var(--line)] bg-white p-5"><div className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">Estimated environmental impact</div><div className="mt-2 text-xl font-semibold">{`${Number(environmental.liters_saved ?? 0).toFixed(1)} L`}</div><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{String(environmental.narrative ?? "Available after analysis.")}</p></section></div>
      <p className="border-l-2 border-[var(--primary)] bg-[var(--surface-strong)] p-4 text-sm leading-6 text-[var(--muted)]">Limitation: results use seeded, synthetic/simulated scenarios and are not validated on deployed building or facility infrastructure. Impact values use documented assumptions and require human review.</p>
    </div>
  </DashboardShell>;
}
