"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchAnalysisHistory, type AnalysisHistoryItem } from "@/services/analysis";

export function AnalysisHistory() {
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchAnalysisHistory()
      .then(setHistory)
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Could not load history."));
  }, []);

  if (error) {
    return <p className="rounded-[1.6rem] bg-[rgba(195,63,56,0.1)] p-4 text-sm text-[var(--danger)]">{error}</p>;
  }

  return (
    <div className="grid gap-4">
      {history.map((item) => (
        <Link key={item.analysis_id} href={`/analyses/${item.analysis_id}`} className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5 transition hover:border-[var(--primary)]">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">{item.analysis_id}</div>
              <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em]">{item.scenario_selected}</h3>
            </div>
            <div className="rounded-full bg-[var(--surface-strong)] px-4 py-2 text-sm text-[var(--foreground)]">{item.has_leak ? "Leak detected" : "Stable"}</div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-4 text-sm text-[var(--muted)]">
            <span>Confidence: {item.confidence.toFixed(1)}%</span>
            <span>Loss: {item.leak_lpm.toFixed(1)} L/m</span>
            <span>Total: {item.total_liters.toFixed(1)} L</span>
            <span>{new Date(item.created_at).toLocaleString()}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}