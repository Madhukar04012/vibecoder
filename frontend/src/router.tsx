import { createBrowserRouter, Outlet } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import Login from "@/pages/auth/Login";
import Signup from "@/pages/auth/Signup";
import VibeCober from "@/components/VibeCober";

export const router = createBrowserRouter([
  {
    element: (
      <ThemeProvider>
        <AuthProvider>
          <Outlet />
        </AuthProvider>
      </ThemeProvider>
    ),
    children: [
      { path: "/", element: <VibeCober /> },
      { path: "/login", element: <Login /> },
      { path: "/signup", element: <Signup /> },
    ],
  },
]);
