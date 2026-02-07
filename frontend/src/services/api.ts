import axios from "axios";

// Default to the backend API prefix. If you set VITE_API_BASE_URL in .env, include the API prefix
const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const api = axios.create({ baseURL: base });

api.interceptors.request.use((cfg) => {
	const token = window.localStorage.getItem("token");
	if (token) cfg.headers = { ...cfg.headers, Authorization: `Bearer ${token}` };
	return cfg;
});

export default api;
