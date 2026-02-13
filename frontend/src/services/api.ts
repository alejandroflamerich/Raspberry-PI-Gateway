import axios from "axios";

// Default to the backend API prefix. If you set VITE_API_BASE_URL in .env, use it.
// Otherwise derive the host from the current location so the frontend works without a fixed IP.
const defaultHost = `${window.location.protocol}//${window.location.hostname}:8000`;
const base = import.meta.env.VITE_API_BASE_URL || `${defaultHost}/api/v1`;
const api = axios.create({ baseURL: base });

api.interceptors.request.use((cfg) => {
	// Do not attach Authorization header for login or preflight requests
	const url = String(cfg.url || "").toLowerCase();
	if (url.includes('/auth/login') || (cfg.method || '').toLowerCase() === 'options') {
		return cfg;
	}

	const token = window.localStorage.getItem("token");
	if (token) cfg.headers = { ...cfg.headers, Authorization: `Bearer ${token}` };

	return cfg;
});

export default api;
