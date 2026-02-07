/**
 * API client for VibeCober backend
 */

const API_BASE =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export function getApiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

export interface ApiError {
  detail: string | { msg?: string; loc?: string[] }[];
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = getApiUrl(path);
  const token = localStorage.getItem("vibecober_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: { ...headers, ...options.headers },
      credentials: "include",
    });
  } catch (fetchErr) {
    const msg = (fetchErr as Error)?.message ?? String(fetchErr);
    if (msg === "Failed to fetch" || msg.includes("NetworkError") || msg.includes("Load failed")) {
      throw new Error("Cannot connect to server. Is the backend running at " + url + "?");
    }
    throw fetchErr;
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as ApiError;
    let message: string;
    if (body?.detail !== undefined) {
      message =
        typeof body.detail === "string"
          ? body.detail
          : Array.isArray(body.detail)
            ? body.detail.map((d) => (d as { msg?: string }).msg || JSON.stringify(d)).join(", ")
            : res.statusText;
    } else {
      message = res.status === 500
        ? "Server error. Check that the backend and database are running."
        : res.statusText || "Request failed";
    }
    throw new Error(message);
  }

  return res.json().catch(() => {
    throw new Error("Invalid response from server");
  });
}
