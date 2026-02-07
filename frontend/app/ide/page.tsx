'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { IDELayout } from '@/src/ide/layout/IDELayout';
import { AuthUser, useIDE } from '@/src/ide/store';

function toAuthUser(value: unknown): AuthUser | null {
  if (typeof value !== 'object' || value === null) return null;
  const v = value as Record<string, unknown>;

  const idRaw = v.id;
  const id = typeof idRaw === 'string' ? idRaw : idRaw != null ? String(idRaw) : undefined;
  const email = typeof v.email === 'string' ? v.email : undefined;
  const name = typeof v.name === 'string' ? v.name : v.name == null ? null : String(v.name);
  const createdAt = typeof v.created_at === 'string' ? v.created_at : undefined;

  return { id, email, name, created_at: createdAt };
}

export default function IdePage() {
  const router = useRouter();
  const setAuth = useIDE((s) => s.setAuth);
  const toggleDB = useIDE((s) => s.toggleDB);

  useEffect(() => {
    // Token handoff from landing page happens via URL hash:
    //   /ide#access_token=...
    const hash = typeof window !== 'undefined' ? window.location.hash : '';
    const match = hash.match(/access_token=([^&]+)/);
    const accessToken = match ? decodeURIComponent(match[1]) : null;

    // If we didn't receive a fresh token in the hash, fall back to the token
    // already stored on the IDE origin.
    let tokenToUse = accessToken;
    if (!tokenToUse) {
      try {
        tokenToUse = localStorage.getItem('access_token');
      } catch {
        tokenToUse = null;
      }
    }

    if (accessToken) {
      try {
        localStorage.setItem('access_token', accessToken);
      } catch {
        // ignore storage errors
      }

      // Clean the hash so it doesn't stick around in the URL.
      router.replace('/ide');
    }

    if (!tokenToUse) return;

    // Fetch user details to confirm DB-backed auth and persist for UI usage.
    fetch('http://127.0.0.1:8000/auth/me', {
      headers: {
        Authorization: `Bearer ${tokenToUse}`,
      },
    })
      .then(async (r) => {
        const text = await r.text();
        let data: unknown = null;
        try {
          data = text ? (JSON.parse(text) as unknown) : null;
        } catch {
          data = null;
        }

        const detail =
          typeof data === 'object' && data !== null && 'detail' in data
            ? (data as { detail?: unknown }).detail
            : null;

        if (!r.ok) {
          throw new Error((detail != null ? String(detail) : '') || text || `auth/me failed (${r.status})`);
        }
        return data;
      })
      .then((user) => {
        const authUser = toAuthUser(user);
        setAuth(tokenToUse, authUser);
        toggleDB(true);
        try {
          localStorage.setItem('current_user', JSON.stringify(authUser));
        } catch {
          // ignore
        }
      })
      .catch(() => {
        setAuth(tokenToUse, null);
        toggleDB(false);
      });
  }, [router, setAuth, toggleDB]);

  return <IDELayout />;
}