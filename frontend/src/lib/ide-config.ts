/**
 * IDE user config - personalize your workspace.
 * When you add auth/login, the logged-in user's name will override this.
 */

const STORAGE_KEY = "vibecober_display_name";

export function getDisplayName(): string {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored?.trim()) return stored.trim();
  }
  return "You";
}

export function setDisplayName(name: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, name.trim());
  }
}
