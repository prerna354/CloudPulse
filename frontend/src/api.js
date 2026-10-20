const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_BASE = BASE.replace(/^http/, "ws");

let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };
export const getToken = () => localStorage.getItem("cp_token");
export const setToken = (token) =>
  token ? localStorage.setItem("cp_token", token) : localStorage.removeItem("cp_token");

async function request(path, options = {}) {
  const token = getToken();
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch {
    throw new Error("Cannot reach the server. Check that the backend is running.");
  }
  if (response.status === 401 && path !== "/api/auth/login") {
    onUnauthorized();
    throw new Error("Your session expired. Please sign in again.");
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (Array.isArray(detail)) throw new Error(detail.map((d) => d.msg).join(", "));
    throw new Error("Something went wrong. Please try again.");
  }
  return data;
}

const query = (params) => new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null)).toString();
const json = (method, body) => ({ method, body: JSON.stringify(body) });

export const api = {
  login: (email, password) => request("/api/auth/login", json("POST", { email, password })),
  summary: () => request("/api/dashboard/summary"),
  services: (params) => request(`/api/services?${query(params)}`),
  createService: (body) => request("/api/services", json("POST", body)),
  updateService: (id, body) => request(`/api/services/${id}`, json("PATCH", body)),
  deleteService: (id) => request(`/api/services/${id}`, { method: "DELETE" }),
  results: (id) => request(`/api/services/${id}/results?limit=60`),
  alerts: (params) => request(`/api/alerts?${query(params)}`),
  acknowledge: (id) => request(`/api/alerts/${id}/acknowledge`, { method: "POST" }),
};
