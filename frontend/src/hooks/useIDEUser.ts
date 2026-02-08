import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getMe } from "@/api/auth";
import { getDisplayName } from "@/lib/ide-config";

/**
 * Returns the display name for the IDE top bar.
 * When logged in: uses the user's name from the API.
 * When not logged in: uses the stored display name from ide-config (or "You").
 */
export function useIDEUser(): [string, () => void] {
  const { isAuthenticated } = useAuth();
  const [name, setName] = useState<string>(() => getDisplayName());

  const refresh = useCallback(() => {
    if (isAuthenticated) {
      getMe()
        .then((user) => {
          const display = user.name?.trim() || user.email?.split("@")[0] || "You";
          setName(display);
        })
        .catch(() => setName(getDisplayName()));
    } else {
      setName(getDisplayName());
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return [name, refresh];
}
