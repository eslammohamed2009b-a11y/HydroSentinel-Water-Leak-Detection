import Link from "next/link";

type DemoShellProps = { title: string; children: React.ReactNode };

export function DemoShell({ title, children }: DemoShellProps) {
  return (
    <main className="min-h-screen">
      <header className="border-b border-[var(--line)] bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 md:px-8">
          <Link className="font-semibold tracking-tight text-[var(--primary)]" href="/demo">HydroSentinel</Link>
          <nav className="flex items-center gap-1 text-sm text-[var(--muted)]">
            <Link className="rounded-md px-3 py-2 hover:bg-[var(--surface-strong)]" href="/demo">Analyze</Link>
            <Link className="rounded-md px-3 py-2 hover:bg-[var(--surface-strong)]" href="/login">Sign in</Link>
          </nav>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-5 py-8 md:px-8">
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--foreground)]">{title}</h1>
        <div className="mt-6">{children}</div>
      </section>
    </main>
  );
}
