"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { logout } from "@/services/auth";

type DashboardShellProps = { title: string; children: React.ReactNode };

export function DashboardShell({ title, children }: DashboardShellProps) {
  const [authorized, setAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    if (!localStorage.getItem("hydrosentinel_token")) {
      window.location.assign("/login");
      return;
    }
    setAuthorized(true);
  }, []);

  async function handleLogout() {
    const refreshToken = localStorage.getItem("hydrosentinel_refresh_token");
    try { if (refreshToken) await logout(refreshToken); } finally {
      localStorage.removeItem("hydrosentinel_token");
      localStorage.removeItem("hydrosentinel_refresh_token");
      window.location.assign("/login");
    }
  }

  if (authorized !== true) return <main className="grid min-h-screen place-items-center text-sm text-[var(--muted)]">Checking account access…</main>;

  return (
    <main className="min-h-screen">
      <header className="border-b border-[var(--line)] bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 md:px-8">
          <Link className="font-semibold tracking-tight text-[var(--primary)]" href="/dashboard/operational">HydroSentinel</Link>
          <nav className="flex items-center gap-1 text-sm text-[var(--muted)]">
            <Link className="rounded-md px-3 py-2 hover:bg-[var(--surface-strong)]" href="/dashboard/operational">Operational</Link>
            <Link className="rounded-md px-3 py-2 hover:bg-[var(--surface-strong)]" href="/admin/history">History</Link>
            <button className="rounded-md px-3 py-2 hover:bg-[var(--surface-strong)]" onClick={() => void handleLogout()} type="button">Sign out</button>
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
