"use client";

import { FormEvent, useState, useTransition } from "react";

import { login } from "@/services/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@hydrosentinel.app");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        const result = await login({ email, password });
        localStorage.setItem("hydrosentinel_token", result.access_token);
        window.location.href = "/dashboard/operational";
      } catch (submissionError) {
        const message = submissionError instanceof Error ? submissionError.message : "Login failed.";
        setError(message);
      }
    });
  }

  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-[2rem] border border-[var(--line)] bg-[var(--surface)] p-8 shadow-[0_24px_80px_rgba(20,33,24,0.08)] md:p-12">
          <span className="inline-flex rounded-full bg-[rgba(15,92,69,0.1)] px-4 py-2 text-sm font-semibold uppercase tracking-[0.25em] text-[var(--primary)]">
            HydroSentinel Control Room
          </span>
          <h1 className="mt-6 max-w-2xl text-5xl font-semibold leading-[1.02] tracking-[-0.04em] text-[var(--foreground)]">
            Water-risk monitoring rebuilt for operators, leadership, and audit trails.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-[var(--muted)]">
            The new platform separates AI scoring, API workflows, authentication, and reporting so school infrastructure teams can move from demo tooling to production operations.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            <div className="rounded-[1.5rem] bg-[var(--surface-strong)] p-5">
              <div className="text-sm uppercase tracking-[0.18em] text-[var(--muted)]">AI Engine</div>
              <div className="mt-2 text-3xl font-semibold text-[var(--primary)]">Python</div>
            </div>
            <div className="rounded-[1.5rem] bg-[var(--surface-strong)] p-5">
              <div className="text-sm uppercase tracking-[0.18em] text-[var(--muted)]">API</div>
              <div className="mt-2 text-3xl font-semibold text-[var(--primary)]">FastAPI</div>
            </div>
            <div className="rounded-[1.5rem] bg-[var(--surface-strong)] p-5">
              <div className="text-sm uppercase tracking-[0.18em] text-[var(--muted)]">Frontend</div>
              <div className="mt-2 text-3xl font-semibold text-[var(--primary)]">Next.js 15</div>
            </div>
          </div>
        </section>

        <section className="rounded-[2rem] border border-[rgba(20,33,24,0.08)] bg-[rgba(255,253,248,0.92)] p-8 shadow-[0_20px_50px_rgba(20,33,24,0.06)] backdrop-blur">
          <h2 className="text-2xl font-semibold tracking-[-0.03em]">Sign in</h2>
          <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
            Use the backend JWT login endpoint to access analysis history, future feedback tools, and protected admin pages.
          </p>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[var(--muted)]">Email</span>
              <input
                className="w-full rounded-2xl border border-[var(--line)] bg-white px-4 py-3 outline-none ring-0"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[var(--muted)]">Password</span>
              <input
                className="w-full rounded-2xl border border-[var(--line)] bg-white px-4 py-3 outline-none ring-0"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
              />
            </label>
            {error ? <p className="rounded-2xl bg-[rgba(195,63,56,0.1)] px-4 py-3 text-sm text-[var(--danger)]">{error}</p> : null}
            <button
              className="w-full rounded-2xl bg-[var(--primary)] px-4 py-3 font-semibold text-white transition hover:bg-[var(--primary-strong)] disabled:opacity-60"
              disabled={isPending}
              type="submit"
            >
              {isPending ? "Signing in..." : "Enter the dashboard"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}