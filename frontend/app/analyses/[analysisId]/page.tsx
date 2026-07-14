import Link from "next/link";

import { AnalysisDetail } from "@/components/analysis-detail";

export default async function AnalysisDetailPage({ params }: { params: Promise<{ analysisId: string }> }) {
  const { analysisId } = await params;

  return (
    <main className="min-h-screen px-4 py-5 md:px-8 md:py-8">
      <div className="mx-auto max-w-7xl grid gap-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.32em] text-[var(--muted)]">Analysis Detail</div>
            <h1 className="mt-3 text-5xl font-semibold tracking-[-0.05em]">Run {analysisId}</h1>
          </div>
          <Link className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-4 py-2 text-sm text-[var(--foreground)]" href="/admin/history">
            Back to history
          </Link>
        </div>
        <AnalysisDetail analysisId={analysisId} />
      </div>
    </main>
  );
}