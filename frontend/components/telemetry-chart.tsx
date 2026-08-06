export type TelemetryPoint = {
  Timestamp: string;
  Flow_Rate_LPM: number;
  Avg_Pressure_PSI: number;
  Leak_Flag?: boolean;
};

type TelemetryChartProps = { points: TelemetryPoint[] };

function downsample(points: TelemetryPoint[], limit = 200) {
  if (points.length <= limit) return points;

  const important = new Set<number>([0, points.length - 1]);
  points.forEach((point, index) => {
    if (point.Leak_Flag) important.add(index);
  });

  const remaining = Math.max(limit - important.size, 0);
  if (remaining) {
    const stride = Math.max(1, Math.ceil((points.length - 2) / remaining));
    for (let index = 1; index < points.length - 1; index += stride) important.add(index);
  }

  return [...important]
    .sort((first, second) => first - second)
    .slice(0, limit)
    .map((index) => points[index]);
}

function valueRange(values: number[]) {
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const padding = Math.max((maximum - minimum) * 0.1, 0.5);
  return { minimum: Math.max(0, minimum - padding), maximum: maximum + padding };
}

function SignalChart({
  points,
  label,
  unit,
  color,
  valueFor,
}: {
  points: TelemetryPoint[];
  label: string;
  unit: string;
  color: string;
  valueFor: (point: TelemetryPoint) => number;
}) {
  const width = 900;
  const height = 154;
  const padding = { top: 20, right: 58, bottom: 20, left: 54 };
  const range = valueRange(points.map(valueFor));
  const coordinates = points.map((point, index) => {
    const x = padding.left + (index / Math.max(points.length - 1, 1)) * (width - padding.left - padding.right);
    const y = height - padding.bottom - ((valueFor(point) - range.minimum) / Math.max(range.maximum - range.minimum, 1)) * (height - padding.top - padding.bottom);
    return { point, x, y };
  });
  const path = coordinates.map(({ x, y }, index) => `${index ? "L" : "M"}${x},${y}`).join(" ");

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-4 text-xs">
        <span className="font-semibold text-[var(--foreground)]">{label} <span className="font-normal text-[var(--muted)]">({unit})</span></span>
        <span className="text-[var(--muted)]">{range.minimum.toFixed(1)}–{range.maximum.toFixed(1)} {unit}</span>
      </div>
      <svg className="h-auto w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${label} over the telemetry timeline`}>
        {[0.25, 0.5, 0.75].map((fraction) => (
          <line
            key={fraction}
            x1={padding.left}
            x2={width - padding.right}
            y1={padding.top + fraction * (height - padding.top - padding.bottom)}
            y2={padding.top + fraction * (height - padding.top - padding.bottom)}
            stroke="#dce3df"
            strokeDasharray="4 6"
          />
        ))}
        <path d={path} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        {coordinates.filter(({ point }) => point.Leak_Flag).map(({ point, x, y }, index) => (
          <circle key={`${point.Timestamp}-${index}`} cx={x} cy={y} r="4.5" fill="#c33f38" stroke="#ffffff" strokeWidth="2" />
        ))}
      </svg>
    </div>
  );
}

export function TelemetryChart({ points }: TelemetryChartProps) {
  if (!points.length) {
    return <div className="border border-dashed border-[var(--line)] p-5 text-sm text-[var(--muted)]">Telemetry will appear after analysis.</div>;
  }

  const displayed = downsample(points);
  return (
    <section className="border border-[var(--line)] bg-white p-5">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">Diagnostic evidence</div>
          <h2 className="mt-1 text-lg font-semibold">Flow and pressure profile</h2>
        </div>
        <div className="flex items-center gap-4 text-xs text-[var(--muted)]">
          <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[var(--primary)]" />Flow rate</span>
          <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[var(--accent)]" />Average pressure</span>
          <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[var(--danger)]" />Flagged sample</span>
        </div>
      </div>
      <div className="grid gap-5">
        <SignalChart points={displayed} label="Flow rate" unit="L/min" color="#0f5c45" valueFor={(point) => point.Flow_Rate_LPM} />
        <SignalChart points={displayed} label="Average pressure" unit="PSI" color="#c87b2d" valueFor={(point) => point.Avg_Pressure_PSI} />
      </div>
      <p className="mt-4 text-xs text-[var(--muted)]">Showing {displayed.length} of {points.length} samples. First, last, and flagged samples are preserved.</p>
    </section>
  );
}
