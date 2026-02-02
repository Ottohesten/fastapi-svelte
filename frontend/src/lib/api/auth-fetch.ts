import { env } from '$env/dynamic/private';

export async function authFetch(
	fetchFn: typeof fetch,
	url: string,
	options: RequestInit & {
		getAuthToken: () => string | undefined;
		setAuthToken: (t: string) => void;
		getRefreshToken?: () => string | undefined;
		setRefreshToken?: (t: string) => void;
	}
) {
	const token = options.getAuthToken();
	const headers = new Headers(options.headers || {});
	if (token) headers.set('Authorization', `Bearer ${token}`);
	let res = await fetchFn(url, { ...options, headers });
	if (res.status !== 401) return res;
	// try refresh
	const refresh = options.getRefreshToken?.();
	if (!refresh) return res;
	const refreshRes = await fetchFn(`${env.BACKEND_HOST || 'http://127.0.0.1:8000'}/login/refresh`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ refresh_token: refresh })
	});
	if (!refreshRes.ok) return res;
	const json = await refreshRes.json();
	const newAccess = json.access_token as string | undefined;
	const newRefresh = json.refresh_token as string | undefined;
	if (newAccess) options.setAuthToken(newAccess);
	if (newRefresh && options.setRefreshToken) options.setRefreshToken(newRefresh);
	const retryHeaders = new Headers(options.headers || {});
	if (newAccess) retryHeaders.set('Authorization', `Bearer ${newAccess}`);
	return fetchFn(url, { ...options, headers: retryHeaders });
}
