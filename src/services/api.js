import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 15000,
  headers: { "Content-Type": "application/json" }
});

// Keep all backend communication in this file.
export const getHealth = () => api.get("/api/health");
export const getDashboardSummary = () => api.get("/api/dashboard/summary");

export const getStations = (params = {}) =>
  api.get("/api/stations", { params });
export const getStation = (stationId) =>
  api.get(`/api/stations/${encodeURIComponent(stationId)}`);
export const getStationReliability = (stationId) =>
  api.get(`/api/stations/${encodeURIComponent(stationId)}/reliability`);

export const getAlerts = (params = {}) => api.get("/api/alerts", { params });
export const getAlert = (alertId) =>
  api.get(`/api/alerts/${encodeURIComponent(alertId)}`);

export const getMaintenance = (params = {}) =>
  api.get("/api/maintenance", { params });
export const createMaintenance = (payload) =>
  api.post("/api/maintenance", payload);
export const updateMaintenance = (maintenanceId, payload) =>
  api.patch(`/api/maintenance/${encodeURIComponent(maintenanceId)}`, payload);

export function getErrorMessage(error) {
  if (error.response) {
    return error.response.data?.detail || `Server error (${error.response.status})`;
  }
  if (error.request) return "Cannot reach the backend. Check that FastAPI is running.";
  return error.message || "Something went wrong.";
}

export function unwrapList(data) {
  if (Array.isArray(data)) return data;
  if (!data || typeof data !== "object") return [];
  for (const key of ["items", "results", "data", "stations", "alerts", "maintenance", "maintenance_records"]) {
    if (Array.isArray(data[key])) return data[key];
  }
  return [];
}

export default api;
