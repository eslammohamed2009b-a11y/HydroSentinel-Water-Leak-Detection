const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT_MS = 25_000;

function redirectToLogin() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("hydrosentinel_token");
  localStorage.removeItem("hydrosentinel_refresh_token");
  if (window.location.pathname !== "/login") window.location.assign("/login");
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const accessToken = typeof window === "undefined" ? null : localStorage.getItem("hydrosentinel_token");
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw new Error("The analysis service is taking longer than expected. Please try again in a moment.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }

  if (!response.ok) {
    if (response.status === 401) redirectToLogin();
    const payload = await response.text();
    throw new Error(payload || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}
