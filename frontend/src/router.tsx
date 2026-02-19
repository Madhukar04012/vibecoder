/**
 * Router — Auth-gated IDE access
 * 
 * /        → Landing page (public)
 * /login   → Login (public)
 * /signup  → Signup (public)
 * /ide     → IDE (requires auth → redirects to /login if not logged in)
 * /dashboard → Dashboard (requires auth)
 */

import { createBrowserRouter, Outlet, Navigate } from "react-router-dom";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/react";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Login from "@/pages/auth/Login";
import Signup from "@/pages/auth/Signup";
import Dashboard from "@/pages/Dashboard";
import VibeCober from "@/components/VibeCober";
import NovaIDE from "@/components/NovaIDE";

/** Wrapper that redirects to /login if user is not authenticated */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

/** Wrapper that redirects to /ide if user is already authenticated */
function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/ide" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    element: (
      <ThemeProvider>
        <AuthProvider>
          <Outlet />
          <Analytics />
          <SpeedInsights />
        </AuthProvider>
      </ThemeProvider>
    ),
    children: [
      // Public: Landing page
      { path: "/", element: <VibeCober /> },

      // Auth pages: redirect to IDE if already logged in
      {
        path: "/login",
        element: (
          <RedirectIfAuth>
            <Login />
          </RedirectIfAuth>
        ),
      },
      {
        path: "/signup",
        element: (
          <RedirectIfAuth>
            <Signup />
          </RedirectIfAuth>
        ),
      },

      // Protected: IDE (main app)
      {
        path: "/ide",
        element: (
          <RequireAuth>
            <NovaIDE />
          </RequireAuth>
        ),
      },

      // Protected: Dashboard
      {
        path: "/dashboard",
        element: (
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        ),
      },
    ],
  },
]);
