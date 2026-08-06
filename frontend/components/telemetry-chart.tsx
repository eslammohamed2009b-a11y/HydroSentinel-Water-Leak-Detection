type TelemetryPoint = { Timestamp: string; Flow_Rate_LPM: number; Leak_Flag?: boolean };
type TelemetryChartProps = { points: TelemetryPoint[] };

function downsample(points: TelemetryPoint[], limit = 200) {
  if (points.length <= limit) return points;
  const important = new Set<number>([0, points.length - 1]);
  points.forEach((point, index) => { if (point.Leak_Flag) important.add(index); });
  const stride = Math.max(1, Math.ceil(points.length / Math.max(limit - important.size, 1)));
  for (let index = 0; index < points.length; index += stride) important.add(index);
  return [...important].sort((a, b) => a - b).slice(0, limit).map((index) => points[index]);
}

export function TelemetryChart({ points }: TelemetryChartProps) {
  if (!points.length) return <div className="border border-dashed border-[var(--line)] p-5 text-sm text-[var(--muted)]">Telemetry will appear after analysis.</div>;
  const displayed = downsample(points);
  const width = 900, height = 260, padding = 24;
  const maxY = Math.max(...displayed.map((point) => point.Flow_Rate_LPM), 1);
  const coordinates = displayed.map((point, index) => ({ point, x: padding + (index / Math.max(displayed.length - 1, 1)) * (width - padding * 2), y: height - padding - (point.Flow_Rate_LPM / maxY) * (height - padding * 2) }));
  const path = coordinates.map(({ x, y }, index) => `${index ? "L" : "M"}${x},${y}`).join(" ");
  return <section className="border border-[var(--line)] bg-white p-5"><div className="mb-4"><div className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">Telemetry</div><h2 className="mt-1 text-lg font-semibold">Flow profile</h2></div><svg className="h-auto w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Telemetry chart"><path d={path} fill="none" stroke="#0f5c45" strokeWidth="3" strokeLinecap="round" />{coordinates.filter(({ point }) => point.Leak_Flag).map(({ point, x, y }, index) => <circle key={`${point.Timestamp}-${index}`} cx={x} cy={y} r="4" fill="#c33f38" />)}</svg><p className="mt-3 text-xs text-[var(--muted)]">Showing {displayed.length} of {points.length} samples; flagged samples are marked.</p></section>;
}
