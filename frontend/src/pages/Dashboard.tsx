import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DottedSurface } from "@/components/ui/dotted-surface";
import { Home, LogOut, Sun, Moon, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";
import { getMe, type UserResponse } from "@/api/auth";

export default function Dashboard() {
  const { theme, toggleTheme } = useTheme();
  const { logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    getMe()
      .then(setUser)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load user"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (!isAuthenticated) return null;

  return (
    <div className="relative min-h-screen overflow-hidden">
      <DottedSurface className="opacity-90" />
      <div
        aria-hidden="true"
        className={cn(
          "pointer-events-none fixed inset-0 z-[1]",
          "bg-[radial-gradient(ellipse_at_center,hsl(var(--foreground)/0.06),transparent_60%)]",
          "blur-[15px]"
        )}
      />
      <div
        className={cn(
          "pointer-events-none fixed inset-0 z-[2]",
          theme === "dark"
            ? "bg-gradient-to-b from-black/40 via-zinc-900/20 to-black/50"
            : "bg-gradient-to-b from-white/40 via-zinc-100/20 to-white/50"
        )}
      />

      <Link
        to="/"
        aria-label="Back to home"
        className={cn(
          "fixed top-6 left-6 z-50 flex items-center gap-2 px-4 py-2 rounded-lg",
          "backdrop-blur-md border transition-colors",
          theme === "dark"
            ? "bg-white/10 hover:bg-white/20 border-white/20 text-white"
            : "bg-black/5 hover:bg-black/10 border-gray-200 text-gray-900"
        )}
      >
        <Home className="w-4 h-4" />
        Home
      </Link>

      <Button
        variant="outline"
        size="icon"
        onClick={toggleTheme}
        className={cn(
          "fixed top-6 right-6 z-50 rounded-full backdrop-blur-lg",
          theme === "dark"
            ? "bg-black/30 border-white/10 hover:bg-black/40"
            : "bg-white/80 border-gray-200/80 hover:bg-white"
        )}
        aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      >
        {theme === "dark" ? (
          <Sun className="w-4 h-4 text-white" />
        ) : (
          <Moon className="w-4 h-4 text-gray-700" />
        )}
      </Button>

      <div className="relative z-10 min-h-screen flex items-center justify-center px-6">
        <Card
          className={cn(
            "w-full max-w-md backdrop-blur",
            theme === "dark"
              ? "bg-zinc-900/95 border-zinc-800"
              : "bg-white/95 border-zinc-200"
          )}
        >
          <CardHeader className="space-y-1">
            <CardTitle
              className={cn(
                "text-2xl flex items-center gap-2",
                theme === "dark" ? "text-white" : "text-gray-900"
              )}
            >
              <CheckCircle2 className="w-7 h-7 text-green-500" />
              Dashboard
            </CardTitle>
            <CardDescription
              className={theme === "dark" ? "text-zinc-400" : "text-gray-500"}
            >
              {loading ? "Loading..." : error ? "Error loading profile" : "You're logged in successfully"}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {loading && (
              <div className="flex justify-center py-8">
                <span className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            )}

            {error && (
              <div
                className={cn(
                  "rounded-lg px-4 py-3 text-sm",
                  theme === "dark" ? "bg-red-500/20 text-red-400" : "bg-red-50 text-red-600"
                )}
              >
                {error}
              </div>
            )}

            {user && !loading && (
              <div
                className={cn(
                  "rounded-lg px-4 py-3 space-y-1",
                  theme === "dark" ? "bg-zinc-800/80" : "bg-gray-50"
                )}
              >
                <p className="text-sm font-medium">
                  {user.name || "User"}
                </p>
                <p className={cn(
                  "text-sm",
                  theme === "dark" ? "text-zinc-400" : "text-gray-500"
                )}>
                  {user.email}
                </p>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Log out
              </Button>
              <Link to="/">
                <Button className="flex-1">
                  <Home className="w-4 h-4 mr-2" />
                  Go to app
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
