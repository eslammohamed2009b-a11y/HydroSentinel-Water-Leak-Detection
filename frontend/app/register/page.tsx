"use client";

import { FormEvent, useState, useTransition } from "react";

import { register } from "@/services/auth";

export default function RegisterPage() {
  const [email, setEmail] = useState("operator@hydrosentinel.app");
  const [fullName, setFullName] = useState("School Operator");
  const [password, setPassword] = useState("ChangeMe123!");
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    startTransition(async () => {
      try {
        const user = await register({ email, full_name: fullName, password });
        setMessage(`Created user ${user.email}`);
      } catch (submissionError) {
        setMessage(submissionError instanceof Error ? submissionError.message : "Registration failed.");
      }
    });
  }

  return (
    <main className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-2xl rounded-[2rem] border border-[var(--line)] bg-[var(--surface)] p-8 shadow-[0_24px_80px_rgba(20,33,24,0.08)] md:p-12">
        <div className="text-xs uppercase tracking-[0.32em] text-[var(--muted)]">User Provisioning</div>
        <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em]">Create an operator account</h1>
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <input className="w-full rounded-2xl border border-[var(--line)] bg-white px-4 py-3" value={fullName} onChange={(event) => setFullName(event.target.value)} type="text" />
          <input className="w-full rounded-2xl border border-[var(--line)] bg-white px-4 py-3" value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
          <input className="w-full rounded-2xl border border-[var(--line)] bg-white px-4 py-3" value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
          <button className="w-full rounded-2xl bg-[var(--primary)] px-4 py-3 font-semibold text-white disabled:opacity-60" disabled={isPending} type="submit">
            {isPending ? "Creating..." : "Create account"}
          </button>
        </form>
        {message ? <p className="mt-5 text-sm text-[var(--muted)]">{message}</p> : null}
      </div>
    </main>
  );
}