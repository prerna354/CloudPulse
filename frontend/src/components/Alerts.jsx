import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { EmptyState, ErrorState, Spinner, timeAgo } from "./ui";

export default function Alerts({ refreshKey, notify }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [activeOnly, setActiveOnly] = useState(true);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    try {
      setError("");
      setData(await api.alerts({ active_only: activeOnly, page, page_size: 10 }));
    } catch (err) {
      setError(err.message);
    }
  }, [activeOnly, page]);

  useEffect(() => { load(); }, [load, refreshKey]);

  const acknowledge = async (alert) => {
    try { await api.acknowledge(alert.id); load(); } catch (err) { notify(err.message, "error"); }
  };

  return (
    <div className="card">
      <div className="toolbar">
        <label className="check"><input type="checkbox" checked={activeOnly} onChange={(e) => { setActiveOnly(e.target.checked); setPage(1); }} /> Show open alerts only</label>
      </div>
      {error ? <ErrorState message={error} onRetry={load} /> : !data ? <Spinner /> : data.items.length === 0 ? (
        <EmptyState title="No alerts" hint="Alerts appear here when a service goes down or becomes slow." />
      ) : (
        <ul className="alerts">
          {data.items.map((a) => (
            <li key={a.id} className={`alert alert-${a.severity}`}>
              <div>
                <strong>{a.message}</strong>
                <div className="muted small">
                  Opened {timeAgo(a.created_at)} · {a.resolved_at ? `resolved ${timeAgo(a.resolved_at)}` : "still open"}
                </div>
              </div>
              {!a.acknowledged && !a.resolved_at
                ? <button className="btn small-btn" onClick={() => acknowledge(a)}>Acknowledge</button>
                : <span className="muted small">{a.acknowledged ? "Acknowledged" : ""}</span>}
            </li>
          ))}
        </ul>
      )}
      {data && data.total > 10 && (
        <div className="pager">
          <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>Page {page}</span>
          <button className="btn" disabled={page * 10 >= data.total} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
