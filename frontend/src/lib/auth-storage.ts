/**
 * Auth token storage - single source of truth for localStorage key and accessors.
 * No API or React dependencies to avoid circular imports.
 */

export const AUTH_TOKEN_KEY = "vibecober_token";

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } catch {
    // Storage full or unavailable (e.g. private browsing); ignore
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch {
    // Ignore
  }
}
