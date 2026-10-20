/** Dependency-free SVG line chart of response times. Failed checks are drawn as red dots. */
export default function Chart({ results }) {
  if (!results.length) return <p className="muted">No checks recorded yet.</p>;
  const width = 640, height = 200, pad = 28;
  const max = Math.max(...results.map((r) => r.response_ms), 100);
  const x = (i) => pad + (i * (width - pad * 2)) / Math.max(results.length - 1, 1);
  const y = (ms) => height - pad - (ms / max) * (height - pad * 2);
  const path = results.map((r, i) => `${i ? "L" : "M"}${x(i)},${y(r.response_ms)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart" role="img" aria-label="Response time chart">
      <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#cbd5e1" />
      <text x={4} y={pad} fontSize="11" fill="#64748b">{max} ms</text>
      <text x={4} y={height - pad} fontSize="11" fill="#64748b">0</text>
      <path d={path} fill="none" stroke="#2563eb" strokeWidth="2" />
      {results.map((r, i) => !r.is_up && <circle key={i} cx={x(i)} cy={y(r.response_ms)} r="3.5" fill="#dc2626" />)}
    </svg>
  );
}
