import { useState } from "react";
import { api } from "../api";

export default function ServiceModal({ service, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: service?.name ?? "",
    url: service?.url ?? "https://",
    check_interval_seconds: service?.check_interval_seconds ?? 30,
    timeout_ms: service?.timeout_ms ?? 5000,
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setSaving(true);
    const body = {
      ...form,
      check_interval_seconds: Number(form.check_interval_seconds),
      timeout_ms: Number(form.timeout_ms),
    };
    try {
      if (service) await api.updateService(service.id, body);
      else await api.createService(body);
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="overlay" onClick={onClose}>
      <form className="card modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2>{service ? "Edit service" : "Add service"}</h2>
        <label>Name<input value={form.name} onChange={set("name")} required minLength={2} /></label>
        <label>URL to check<input type="url" value={form.url} onChange={set("url")} required /></label>
        <div className="row">
          <label>Check every (seconds)<input type="number" min="10" max="3600" value={form.check_interval_seconds} onChange={set("check_interval_seconds")} /></label>
          <label>Timeout (ms)<input type="number" min="500" max="30000" value={form.timeout_ms} onChange={set("timeout_ms")} /></label>
        </div>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="row end">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
        </div>
      </form>
    </div>
  );
}
