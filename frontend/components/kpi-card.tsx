type KpiCardProps = {
  label: string;
  value: string;
  note: string;
  tone?: "default" | "danger" | "success" | "accent";
};

const toneClasses: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  default: "border-[var(--line)]",
  danger: "border-[rgba(195,63,56,0.25)] bg-[rgba(195,63,56,0.04)]",
  success: "border-[rgba(49,120,87,0.25)] bg-[rgba(49,120,87,0.05)]",
  accent: "border-[rgba(200,123,45,0.3)] bg-[rgba(200,123,45,0.06)]",
};

export function KpiCard({ label, value, note, tone = "default" }: KpiCardProps) {
  return (
    <article className={`rounded-[1.6rem] border p-5 ${toneClasses[tone]}`}>
      <div className="text-xs uppercase tracking-[0.26em] text-[var(--muted)]">{label}</div>
      <div className="mt-3 text-4xl font-semibold tracking-[-0.05em] text-[var(--foreground)]">{value}</div>
      <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{note}</p>
    </article>
  );
}