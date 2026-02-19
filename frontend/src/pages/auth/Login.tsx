import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Mail, Sparkles } from "lucide-react";
import { AnimatedAuthLayout } from "@/components/animated-auth-layout";
import { useAuth } from "@/contexts/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await login({ email, password });
      navigate("/ide");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatedAuthLayout
      brandName="Vibecoder"
      isTyping={isTyping}
      showPassword={showPassword}
      password={password}
    >
      <div className="text-center mb-8 sm:mb-10">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">Welcome back!</h1>
        <p className="text-muted-foreground text-sm">Please enter your details</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-medium">
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="you@vibecober.ai"
            value={email}
            autoComplete="off"
            onChange={(e) => setEmail(e.target.value)}
            onFocus={() => setIsTyping(true)}
            onBlur={() => setIsTyping(false)}
            required
            className="h-12 bg-background border-border/60 focus:border-primary"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-sm font-medium">
            Password
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="h-12 pr-10 bg-background border-border/60 focus:border-primary"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? (
                <EyeOff className="size-5" />
              ) : (
                <Eye className="size-5" />
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="remember"
              checked={rememberMe}
              onCheckedChange={(checked) => setRememberMe(checked === true)}
            />
            <Label
              htmlFor="remember"
              className="text-sm font-normal cursor-pointer"
            >
              Remember for 30 days
            </Label>
          </div>
          <a
            href="#"
            className="text-sm text-primary hover:underline font-medium"
          >
            Forgot password?
          </a>
        </div>

        {error && (
          <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
            {error}
          </div>
        )}

        <Button
          type="submit"
          className="w-full h-12 text-base font-medium touch-manipulation"
          size="lg"
          disabled={isLoading}
        >
          {isLoading ? "Signing in..." : "Log in"}
        </Button>
      </form>

      <div className="mt-6">
        <Button
          variant="outline"
          className="w-full h-12 bg-background border-border/60 hover:bg-accent touch-manipulation"
          type="button"
        >
          <Mail className="mr-2 size-5" />
          Log in with Google
        </Button>
      </div>

      <div className="text-center text-sm text-muted-foreground mt-8">
        Don&apos;t have an account?{" "}
        <Link to="/signup" className="text-foreground font-medium hover:underline">
          Sign Up
        </Link>
      </div>
    </AnimatedAuthLayout>
  );
}
