const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT_MS = 25_000;
const READINESS_TIMEOUT_MS = 5_000;

function redirectToDemo() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("hydrosentinel_token");
  localStorage.removeItem("hydrosentinel_refresh_token");
  if (window.location.pathname !== "/demo") window.location.assign("/demo");
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
    if (response.status === 401) redirectToDemo();
    const payload = await response.text();
    throw new Error(payload || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** Probe the lightweight readiness route with a responsive, abortable timeout. */
export async function isApiReady(signal?: AbortSignal): Promise<boolean> {
  if (signal?.aborted) return false;

  const controller = new AbortController();
  const abortForCaller = () => controller.abort();
  signal?.addEventListener("abort", abortForCaller, { once: true });
  const timeout = window.setTimeout(() => controller.abort(), READINESS_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}/ready`, {
      signal: controller.signal,
      cache: "no-store",
    });
    if (!response.ok) return false;
    const payload = await response.json() as { status?: string };
    return payload.status === "ready";
  } catch {
    return false;
  } finally {
    window.clearTimeout(timeout);
    signal?.removeEventListener("abort", abortForCaller);
  }
}
