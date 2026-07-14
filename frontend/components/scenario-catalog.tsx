"use client";

import { useEffect, useState } from "react";

import { fetchScenarios, type ScenarioSummary } from "@/services/analysis";

export function ScenarioCatalog() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchScenarios()
      .then(setScenarios)
      .catch((loadError) => setError(loadError instanceof Error ? loadError.message : "Could not load scenarios."));
  }, []);

  if (error) {
    return <p className="rounded-[1.6rem] bg-[rgba(195,63,56,0.1)] p-4 text-sm text-[var(--danger)]">{error}</p>;
  }

  return (
    <div className="grid gap-5 md:grid-cols-2">
      {scenarios.map((scenario) => (
        <article key={scenario.slug} className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
          <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">{scenario.filename}</div>
          <h3 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">{scenario.label}</h3>
          <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{scenario.description}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase tracking-[0.18em] text-[var(--muted)]">
            <span className="rounded-full bg-[var(--surface-strong)] px-3 py-2">{scenario.occupancy_mode ?? "normal"}</span>
            <span className="rounded-full bg-[var(--surface-strong)] px-3 py-2">{scenario.expected_has_leak ? "expected leak" : "expected normal"}</span>
          </div>
        </article>
      ))}
    </div>
  );
}