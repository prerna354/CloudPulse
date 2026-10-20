import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import Chart from "./Chart";
import ServiceModal from "./ServiceModal";
import { EmptyState, ErrorState, Spinner, StatusBadge, timeAgo } from "./ui";

const PAGE_SIZE = 8;

export default function Services({ user, refreshKey, notify }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null); // null | "new" | service
  const [detail, setDetail] = useState(null);
  const [results, setResults] = useState([]);
  const isAdmin = user.role === "admin";

  useEffect(() => {
    const timer = setTimeout(() => { setQuery(search); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(async () => {
    try {
      setError("");
      setData(await api.services({ q: query, status, page, page_size: PAGE_SIZE }));
    } catch (err) {
      setError(err.message);
    }
  }, [query, status, page]);

  useEffect(() => { load(); }, [load, refreshKey]);

  const openDetail = async (service) => {
    setDetail(service);
    setResults([]);
    try { setResults(await api.results(service.id)); } catch (err) { notify(err.message, "error"); }
  };

  const remove = async (service) => {
    if (!window.confirm(`Delete "${service.name}" and all of its history?`)) return;
    try {
      await api.deleteService(service.id);
      notify(`${service.name} deleted`, "info");
      load();
    } catch (err) {
      notify(err.message, "error");
    }
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="card">
      <div className="toolbar">
        <input placeholder="Search services..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="up">Up</option><option value="degraded">Degraded</option>
          <option value="down">Down</option><option value="unknown">Unknown</option>
        </select>
        {isAdmin && <button className="btn primary" onClick={() => setEditing("new")}>+ Add service</button>}
      </div>

      {error ? <ErrorState message={error} onRetry={load} /> : !data ? <Spinner /> : data.items.length === 0 ? (
        <EmptyState title="No services found" hint="Try a different search or add a new service to monitor." />
      ) : (
        <div className="table-scroll">
          <table>
            <thead><tr><th>Service</th><th>Status</th><th>Response</th><th>Uptime 24h</th><th>Last check</th><th /></tr></thead>
            <tbody>
              {data.items.map((s) => (
                <tr key={s.id}>
                  <td><button className="link" onClick={() => openDetail(s)}>{s.name}</button><div className="muted small">{s.url}</div></td>
                  <td><StatusBadge status={s.status} /></td>
                  <td>{s.last_response_ms != null ? `${s.last_response_ms} ms` : "-"}</td>
                  <td>{s.uptime_24h != null ? `${s.uptime_24h}%` : "-"}</td>
                  <td>{timeAgo(s.last_checked_at)}</td>
                  <td className="actions">
                    {isAdmin && <>
                      <button className="btn small-btn" onClick={() => setEditing(s)}>Edit</button>
                      <button className="btn small-btn danger" onClick={() => remove(s)}>Delete</button>
                    </>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > PAGE_SIZE && (
        <div className="pager">
          <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>Page {page} of {totalPages}</span>
          <button className="btn" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      )}

      {editing && (
        <ServiceModal
          service={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); notify("Service saved", "info"); load(); }}
        />
      )}

      {detail && (
        <div className="overlay" onClick={() => setDetail(null)}>
          <div className="card modal wide" onClick={(e) => e.stopPropagation()}>
            <h2>{detail.name} <StatusBadge status={detail.status} /></h2>
            <p className="muted small">Response time of the last {results.length} checks (red dots = failed checks)</p>
            <Chart results={results} />
            <div className="row end"><button className="btn" onClick={() => setDetail(null)}>Close</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
