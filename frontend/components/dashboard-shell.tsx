import Link from "next/link";

type DashboardShellProps = {
  title: string;
  eyebrow: string;
  subtitle: string;
  children: React.ReactNode;
  aside: React.ReactNode;
};

export function DashboardShell({ title, eyebrow, subtitle, children, aside }: DashboardShellProps) {
  return (
    <main className="min-h-screen px-4 py-5 md:px-8 md:py-8">
      <div className="mx-auto max-w-7xl shell-grid">
        <aside className="rounded-[2rem] border border-[var(--line)] bg-[rgba(255,253,248,0.82)] p-6 shadow-[0_20px_60px_rgba(20,33,24,0.07)] backdrop-blur">
          <div className="rounded-[1.6rem] bg-[var(--primary)] p-6 text-white">
            <div className="text-xs uppercase tracking-[0.35em] text-white/70">HydroSentinel</div>
            <h1 className="mt-4 text-3xl font-semibold tracking-[-0.04em]">{eyebrow}</h1>
            <p className="mt-3 text-sm leading-7 text-white/78">{subtitle}</p>
          </div>
          <nav className="mt-6 grid gap-3">
            <Link className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 font-medium" href="/dashboard/operational">
              Operational Dashboard
            </Link>
            <Link className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 font-medium" href="/dashboard/executive">
              Executive Summary
            </Link>
            <Link className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 font-medium" href="/login">
              Authentication
            </Link>
          </nav>
          <div className="mt-6 rounded-[1.6rem] bg-[var(--surface-strong)] p-5">
            <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Migration Status</div>
            <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
              This Next.js shell now targets the new FastAPI backend for analysis workflows while the legacy Streamlit app remains available during cutover.
            </p>
          </div>
        </aside>
        <section className="rounded-[2rem] border border-[var(--line)] bg-[rgba(255,253,248,0.82)] p-5 shadow-[0_20px_60px_rgba(20,33,24,0.07)] backdrop-blur md:p-8">
          <header className="mb-6 flex flex-col gap-4 border-b border-[var(--line)] pb-5 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.32em] text-[var(--muted)]">{title}</div>
              <h2 className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-[var(--foreground)]">{eyebrow}</h2>
            </div>
            <div className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-4 py-2 text-sm text-[var(--muted)]">
              Next.js 15 + FastAPI migration track
            </div>
          </header>
          <div className="grid gap-6 xl:grid-cols-[1.65fr_0.85fr]">
            <div>{children}</div>
            <div>{aside}</div>
          </div>
        </section>
      </div>
    </main>
  );
}