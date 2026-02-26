/**
 * API client for VibeCober backend
 */

import { getStoredToken } from "@/lib/auth-storage";

// When served from same origin (single-server mode), use relative URLs
const API_BASE =
  import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? "" : "http://127.0.0.1:8000");

/** Default request timeout in milliseconds. */
const DEFAULT_TIMEOUT_MS = 30_000;

export function getApiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

export interface ApiError {
  detail: string | { msg?: string; loc?: string[] }[];
}

export interface ApiFetchOptions extends RequestInit {
  /** Request timeout in milliseconds (default: 30 000). */
  timeoutMs?: number;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  const url = getApiUrl(path);
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((fetchOptions.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // AbortController: merge caller's signal with a timeout signal
  const timeoutController = new AbortController();
  const timeoutId = setTimeout(() => timeoutController.abort(), timeoutMs);

  // If the caller passed a signal, abort on either the caller's signal or timeout
  const callerSignal = fetchOptions.signal;
  if (callerSignal) {
    callerSignal.addEventListener("abort", () => timeoutController.abort(), { once: true });
  }

  let res: Response;
  try {
    res = await fetch(url, {
      ...fetchOptions,
      headers: { ...headers, ...fetchOptions.headers },
      signal: timeoutController.signal,
    });
  } catch (fetchErr) {
    if (timeoutController.signal.aborted && !callerSignal?.aborted) {
      throw new Error(`Request timed out after ${timeoutMs}ms: ${path}`);
    }
    const msg = (fetchErr as Error)?.message ?? String(fetchErr);
    if (msg === "Failed to fetch" || msg.includes("NetworkError") || msg.includes("Load failed")) {
      throw new Error("Cannot connect to server. Is the backend running at " + url + "?");
    }
    throw fetchErr;
  } finally {
    clearTimeout(timeoutId);
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
