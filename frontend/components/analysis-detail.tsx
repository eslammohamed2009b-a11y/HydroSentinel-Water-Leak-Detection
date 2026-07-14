"use client";

import { useEffect, useState } from "react";

import { KpiCard } from "@/components/kpi-card";
import { TelemetryChart } from "@/components/telemetry-chart";
import { fetchAnalysisById, submitFeedback, type AnalysisResponse } from "@/services/analysis";

export function AnalysisDetail({ analysisId }: { analysisId: string }) {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchAnalysisById(analysisId)
      .then(setResult)
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Could not load analysis."));
  }, [analysisId]);

  async function handleFeedback(verdict: string) {
    try {
      const response = await submitFeedback(analysisId, verdict);
      setFeedbackMessage(`Feedback saved: ${response.feedback}`);
    } catch (feedbackError) {
      setFeedbackMessage(feedbackError instanceof Error ? feedbackError.message : "Could not save feedback.");
    }
  }

  if (error) {
    return <p className="rounded-[1.6rem] bg-[rgba(195,63,56,0.1)] p-4 text-sm text-[var(--danger)]">{error}</p>;
  }

  if (!result) {
    return <p className="rounded-[1.6rem] border border-dashed border-[var(--line)] p-6 text-sm text-[var(--muted)]">Loading analysis...</p>;
  }

  const telemetryPoints = result.telemetry_points.map((point) => ({
    Timestamp: String(point.Timestamp ?? ""),
    Flow_Rate_LPM: Number(point.Flow_Rate_LPM ?? 0),
    Leak_Flag: Boolean(point.Leak_Flag ?? false),
  }));

  return (
    <div className="grid gap-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Analysis" value={result.analysis_id ?? analysisId} note="Stable public identifier for the run." />
        <KpiCard label="Scenario" value={result.scenario_selected ?? "Unknown"} note="Dataset used for this evaluation." />
        <KpiCard label="Leak Type" value={result.leak_type?.replaceAll("_", " ") ?? "None"} note="Top classifier result." />
        <KpiCard label="Confidence" value={`${result.confidence.toFixed(1)}%`} note="Current decision confidence." />
      </div>
      <TelemetryChart points={telemetryPoints} />
      <section className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
        <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Reasoning</div>
        <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{result.reasoning_string}</p>
        <div className="mt-5 flex flex-wrap gap-3">
          <button className="rounded-2xl bg-[var(--primary)] px-4 py-3 text-sm font-semibold text-white" onClick={() => void handleFeedback("confirmed_alert")} type="button">Confirm alert</button>
          <button className="rounded-2xl border border-[var(--line)] px-4 py-3 text-sm font-semibold text-[var(--foreground)]" onClick={() => void handleFeedback("false_positive")} type="button">Mark false positive</button>
        </div>
        {feedbackMessage ? <p className="mt-4 text-sm text-[var(--muted)]">{feedbackMessage}</p> : null}
      </section>
    </div>
  );
}