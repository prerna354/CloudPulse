import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState, ErrorState, Spinner, StatusBadge, timeAgo } from "./ui";

const CARDS = [
  ["total_services", "Services", ""],
  ["up", "Healthy", "good"],
  ["degraded", "Degraded", "warn"],
  ["down", "Down", "bad"],
  ["active_alerts", "Open alerts", "bad"],
];

export default function Dashboard({ refreshKey }) {
  const [summary, setSummary] = useState(null);
  const [problems, setProblems] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setError("");
      const [s, down, degraded] = await Promise.all([
        api.summary(),
        api.services({ status: "down", page_size: 10 }),
        api.services({ status: "degraded", page_size: 10 }),
      ]);
      setSummary(s);
      setProblems([...down.items, ...degraded.items]);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { load(); }, [load, refreshKey]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!summary) return <Spinner />;

  return (
    <>
      <div className="cards">
        {CARDS.map(([key, label, tone]) => (
          <div key={key} className={`card stat ${tone}`}><span>{label}</span><strong>{summary[key]}</strong></div>
        ))}
        <div className="card stat"><span>Uptime (24h)</span><strong>{summary.uptime_24h ?? "-"}{summary.uptime_24h != null && "%"}</strong></div>
        <div className="card stat"><span>Avg response (1h)</span><strong>{summary.avg_response_ms_1h ?? "-"}{summary.avg_response_ms_1h != null && " ms"}</strong></div>
      </div>
      <div className="card">
        <h2>Services needing attention</h2>
        {problems.length === 0 ? (
          <EmptyState title="All systems operational" hint="No service is down or degraded right now." />
        ) : (
          <table>
            <thead><tr><th>Service</th><th>Status</th><th>Response</th><th>Last check</th></tr></thead>
            <tbody>
              {problems.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td><td><StatusBadge status={s.status} /></td>
                  <td>{s.last_response_ms != null ? `${s.last_response_ms} ms` : "-"}</td>
                  <td>{timeAgo(s.last_checked_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
