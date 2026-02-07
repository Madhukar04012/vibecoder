import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DottedSurface } from "@/components/ui/dotted-surface";
import { Home, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";

export default function Signup() {
  const { theme, toggleTheme } = useTheme();
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await signup({ email, password, name: name || undefined });
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

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
                "text-2xl",
                theme === "dark" ? "text-white" : "text-gray-900"
              )}
            >
              Create an account
            </CardTitle>
            <CardDescription
              className={theme === "dark" ? "text-zinc-400" : "text-gray-500"}
            >
              Start building with VibeCober
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
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
              <div className="space-y-2">
                <Label
                  htmlFor="name"
                  className={theme === "dark" ? "text-zinc-300" : "text-gray-600"}
                >
                  Name
                </Label>
                <Input
                  id="name"
                  placeholder="Madhukar Reddy"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                  className={cn(
                    theme === "dark"
                      ? "bg-zinc-800 border-zinc-700 text-white"
                      : "bg-gray-50 border-gray-200 text-gray-900"
                  )}
                />
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="email"
                  className={theme === "dark" ? "text-zinc-300" : "text-gray-600"}
                >
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@vibecober.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className={cn(
                    theme === "dark"
                      ? "bg-zinc-800 border-zinc-700 text-white"
                      : "bg-gray-50 border-gray-200 text-gray-900"
                  )}
                />
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="password"
                  className={theme === "dark" ? "text-zinc-300" : "text-gray-600"}
                >
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  className={cn(
                    theme === "dark"
                      ? "bg-zinc-800 border-zinc-700 text-white"
                      : "bg-gray-50 border-gray-200 text-gray-900"
                  )}
                />
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    Creating account...
                  </span>
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>

            <p
              className={cn(
                "text-sm text-center",
                theme === "dark" ? "text-zinc-400" : "text-gray-500"
              )}
            >
              Already have an account?{" "}
              <Link
                to="/login"
                className={theme === "dark" ? "text-white hover:underline" : "text-gray-900 hover:underline"}
              >
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
