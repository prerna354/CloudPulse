import { useCallback, useEffect, useRef, useState } from "react";
import { api, getToken, setToken, setUnauthorizedHandler } from "./api";
import { useLiveEvents } from "./useLiveEvents";
import Alerts from "./components/Alerts";
import Dashboard from "./components/Dashboard";
import Login from "./components/Login";
import Services from "./components/Services";

const NAV = [["dashboard", "Dashboard"], ["services", "Services"], ["alerts", "Alerts"]];

export default function App() {
  const [user, setUser] = useState(() => {
    try { return getToken() ? JSON.parse(localStorage.getItem("cp_user")) : null; } catch { return null; }
  });
  const [view, setView] = useState("dashboard");
  const [refreshKey, setRefreshKey] = useState(0);
  const [toasts, setToasts] = useState([]);
  const refreshTimer = useRef(null);

  const logout = useCallback(() => {
    setToken(null);
    localStorage.removeItem("cp_user");
    setUser(null);
  }, []);

  useEffect(() => { setUnauthorizedHandler(logout); }, [logout]);

  const notify = useCallback((text, tone = "info") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, text, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  }, []);

  const handleEvent = useCallback((event) => {
    if (event.type === "alert") {
      notify(event.message, event.severity === "critical" ? "error" : event.action === "resolved" ? "info" : "warn");
    }
    clearTimeout(refreshTimer.current); // batch bursts of events into one refresh
    refreshTimer.current = setTimeout(() => setRefreshKey((k) => k + 1), 500);
  }, [notify]);

  const live = useLiveEvents(Boolean(user), handleEvent);

  if (!user) {
    return <Login onLogin={(u) => { localStorage.setItem("cp_user", JSON.stringify(u)); setUser(u); }} />;
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>CloudPulse</h1>
        <nav>
          {NAV.map(([key, label]) => (
            <button key={key} className={view === key ? "active" : ""} onClick={() => setView(key)}>{label}</button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className={`live ${live ? "on" : ""}`}>{live ? "● Live" : "○ Reconnecting..."}</div>
          <div className="small">{user.full_name}<br /><span className="muted">{user.role}</span></div>
          <button className="btn" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main>
        <h2 className="page-title">{NAV.find(([k]) => k === view)[1]}</h2>
        {view === "dashboard" && <Dashboard refreshKey={refreshKey} />}
        {view === "services" && <Services user={user} refreshKey={refreshKey} notify={notify} />}
        {view === "alerts" && <Alerts refreshKey={refreshKey} notify={notify} />}
      </main>
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => <div key={t.id} className={`toast ${t.tone}`}>{t.text}</div>)}
      </div>
    </div>
  );
}
