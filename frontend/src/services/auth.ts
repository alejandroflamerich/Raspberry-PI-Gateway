import api from "./api";

export async function login(username: string, password: string) {
	try {
		console.info("auth.login: sending", { username });
		const r = await api.post("/api/v1/auth/login", { username, password });
		console.info("auth.login: response", { status: r.status, data: r.data });
		const token = r.data.access_token;
		window.localStorage.setItem("token", token);
		return true;
	} catch (e) {
		console.error("auth.login: failed", e);
		return false;
	}
}

export function logout() {
	window.localStorage.removeItem("token");
}
