import { createBrowserRouter, Outlet } from "react-router-dom";
import { Analytics } from "@vercel/analytics/react";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import Login from "@/pages/auth/Login";
import Signup from "@/pages/auth/Signup";
import Dashboard from "@/pages/Dashboard";
import VibeCober from "@/components/VibeCober";

export const router = createBrowserRouter([
  {
    element: (
      <ThemeProvider>
        <AuthProvider>
          <Outlet />
          <Analytics />
        </AuthProvider>
      </ThemeProvider>
    ),
    children: [
      { path: "/", element: <VibeCober /> },
      { path: "/dashboard", element: <Dashboard /> },
      { path: "/login", element: <Login /> },
      { path: "/signup", element: <Signup /> },
    ],
  },
]);
