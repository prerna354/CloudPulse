export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export function Spinner({ label = "Loading..." }) {
  return <div className="state"><div className="spinner" /><p>{label}</p></div>;
}

export function EmptyState({ title, hint }) {
  return <div className="state"><h3>{title}</h3><p>{hint}</p></div>;
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state error">
      <p>{message}</p>
      {onRetry && <button className="btn" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function timeAgo(iso) {
  if (!iso) return "never";
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
