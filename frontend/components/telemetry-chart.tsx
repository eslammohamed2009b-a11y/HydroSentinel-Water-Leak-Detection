type TelemetryPoint = {
  Timestamp: string;
  Flow_Rate_LPM: number;
  Leak_Flag?: boolean;
};

type TelemetryChartProps = {
  points: TelemetryPoint[];
};

export function TelemetryChart({ points }: TelemetryChartProps) {
  if (points.length === 0) {
    return <div className="rounded-[1.6rem] border border-dashed border-[var(--line)] p-6 text-sm text-[var(--muted)]">No telemetry yet.</div>;
  }

  const width = 900;
  const height = 280;
  const padding = 24;
  const maxY = Math.max(...points.map((point) => point.Flow_Rate_LPM), 1);
  const path = points
    .map((point, index) => {
      const x = padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2);
      const y = height - padding - (point.Flow_Rate_LPM / maxY) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  return (
    <div className="rounded-[1.6rem] border border-[var(--line)] bg-[var(--surface)] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-[var(--muted)]">Telemetry</div>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em]">Flow profile</h3>
        </div>
        <div className="rounded-full bg-[rgba(15,92,69,0.08)] px-3 py-1 text-sm text-[var(--primary)]">SVG chart</div>
      </div>
      <svg className="h-auto w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Telemetry chart">
        <rect x="0" y="0" width={width} height={height} rx="24" fill="#f8fbf4" />
        <path d={path} fill="none" stroke="#0f5c45" strokeWidth="4" strokeLinecap="round" />
        {points.map((point, index) => {
          const x = padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2);
          const y = height - padding - (point.Flow_Rate_LPM / maxY) * (height - padding * 2);
          return <circle key={`${point.Timestamp}-${index}`} cx={x} cy={y} r={point.Leak_Flag ? 5 : 3} fill={point.Leak_Flag ? "#c33f38" : "#c87b2d"} />;
        })}
      </svg>
    </div>
  );
}