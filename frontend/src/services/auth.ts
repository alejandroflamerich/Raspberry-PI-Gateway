import api from "./api";
import { useAuth } from "../store/authStore";

export async function login(username: string, password: string) {
	try {
		console.info("auth.login: sending", { username });
		const r = await api.post("/auth/login", { username, password });
		console.info("auth.login: response", { status: r.status, data: r.data });
		const token = r.data.access_token;
		window.localStorage.setItem("token", token);
		// update global store so UI reacts immediately
		try{ useAuth.getState().setToken(token) }catch(e){}
		return true;
	} catch (e) {
		console.error("auth.login: failed", e);
		return false;
	}
}

export function logout() {
	window.localStorage.removeItem("token");
	try{ useAuth.getState().setToken(null) }catch(e){}
}
