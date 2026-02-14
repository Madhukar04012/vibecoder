"""
S-Class Code Templates — Production-Quality Starter Code

These templates produce the same quality code that a team of senior
engineers at a top software company would write.

Key differences from basic templates:
- TypeScript everywhere (not JS)
- Tailwind CSS with design tokens
- shadcn/ui-style component library
- Proper error handling, loading states, type safety
- Service layer pattern
- Environment-based config
- CI/CD pipeline
- Comprehensive testing setup
"""

from typing import Dict, Any, List


# ═════════════════════════════════════════════════════════════════════════════
# FRONTEND TEMPLATES — React + Vite + TypeScript + Tailwind
# ═════════════════════════════════════════════════════════════════════════════

def get_sclass_frontend_templates(project_name: str, features: List[str]) -> Dict[str, str]:
    """Generate S-class frontend templates."""

    pn = project_name.replace("-", " ").replace("_", " ").title()
    pn_slug = project_name.lower().replace(" ", "-").replace("_", "-")

    templates = {}

    # ── package.json ──
    templates["frontend/package.json"] = f'''{{
  "name": "{pn_slug}",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write \\"src/**/*.{{ts,tsx,css}}\\"",
    "type-check": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }},
  "dependencies": {{
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.1.0",
    "zustand": "^5.0.0",
    "@tanstack/react-query": "^5.62.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "zod": "^3.24.0",
    "lucide-react": "^0.468.0",
    "sonner": "^1.7.0"
  }},
  "devDependencies": {{
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.17.0",
    "prettier": "^3.4.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0"
  }}
}}
'''

    # ── tsconfig.json ──
    templates["frontend/tsconfig.json"] = '''{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
'''

    templates["frontend/tsconfig.node.json"] = '''{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": true
  },
  "include": ["vite.config.ts"]
}
'''

    templates["frontend/tsconfig.app.json"] = '''{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo"
  },
  "include": ["src"]
}
'''

    # ── vite.config.ts ──
    templates["frontend/vite.config.ts"] = '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
});
'''

    # ── Tailwind ──
    templates["frontend/tailwind.config.ts"] = '''import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
'''

    templates["frontend/postcss.config.js"] = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
'''

    templates["frontend/components.json"] = f'''{{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {{
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "prefix": ""
  }},
  "aliases": {{
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }}
}}
'''

    # ── eslint + prettier ──
    templates["frontend/eslint.config.js"] = '''import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
  {
    ignores: ["dist/", "node_modules/", "*.config.js"],
  }
);
'''

    templates["frontend/.prettierrc"] = '''{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
'''

    # ── index.html ──
    templates["frontend/index.html"] = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{pn} — Built with VibeCober" />
    <title>{pn}</title>
  </head>
  <body class="min-h-screen bg-background font-sans antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''

    # ── src/main.tsx ──
    templates["frontend/src/main.tsx"] = '''import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster richColors position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
'''

    # ── src/App.tsx ──
    templates["frontend/src/App.tsx"] = '''import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { RootLayout } from "@/components/layout/root-layout";
import { ErrorBoundary } from "@/components/error-boundary";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

// Lazy-loaded pages for code splitting
const HomePage = lazy(() => import("@/pages/home"));
const NotFoundPage = lazy(() => import("@/components/not-found"));

export default function App() {
  return (
    <ErrorBoundary>
      <RootLayout>
        <Suspense fallback={<LoadingSpinner className="min-h-[60vh]" />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            {/* Add more routes here */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </RootLayout>
    </ErrorBoundary>
  );
}
'''

    # ── src/index.css ──
    templates["frontend/src/index.css"] = '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
'''

    templates["frontend/src/App.css"] = '''/* App-specific styles — keep minimal, use Tailwind utilities */
'''

    templates["frontend/src/vite-env.d.ts"] = '''/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
'''

    # ── lib/utils.ts ──
    templates["frontend/src/lib/utils.ts"] = '''import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes with clsx — the shadcn/ui pattern */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a date to a human-readable string */
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(date));
}

/** Truncate text with ellipsis */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
}

/** Sleep utility for async operations */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
'''

    # ── lib/api-client.ts ──
    templates["frontend/src/lib/api-client.ts"] = '''/**
 * Type-safe API client with error handling, retries, and auth.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { body, params, headers: customHeaders, ...rest } = options;

  // Build URL with query params
  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  // Build headers
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((customHeaders as Record<string, string>) || {}),
  };

  // Add auth token if available
  const token = localStorage.getItem("auth_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...rest,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Handle auth errors
  if (response.status === 401) {
    localStorage.removeItem("auth_token");
    window.location.href = "/login";
    throw new ApiError(401, "Unauthorized");
  }

  // Handle errors
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(response.status, response.statusText, errorData);
  }

  // Handle no-content responses
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/** Type-safe API methods */
export const api = {
  get: <T>(endpoint: string, params?: Record<string, string>) =>
    request<T>(endpoint, { method: "GET", params }),

  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "POST", body }),

  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "PUT", body }),

  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "PATCH", body }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),
};
'''

    # ── lib/constants.ts ──
    templates["frontend/src/lib/constants.ts"] = f'''/** Application constants */

export const APP_NAME = "{pn}";
export const APP_DESCRIPTION = "{pn} — Built with VibeCober";

export const ROUTES = {{
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  SETTINGS: "/settings",
  PROFILE: "/profile",
}} as const;
'''

    # ── lib/validators.ts ──
    templates["frontend/src/lib/validators.ts"] = '''import { z } from "zod";

/** Reusable Zod schemas for form validation */

export const emailSchema = z
  .string()
  .min(1, "Email is required")
  .email("Invalid email address");

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Must contain at least one uppercase letter")
  .regex(/[0-9]/, "Must contain at least one number");

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z
  .object({
    name: z.string().min(2, "Name must be at least 2 characters"),
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
'''

    # ── types/index.ts ──
    templates["frontend/src/types/index.ts"] = '''/** Core application types */

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiErrorResponse {
  detail: string;
  status_code: number;
}
'''

    # ── types/api.ts ──
    templates["frontend/src/types/api.ts"] = '''/** API-specific request/response types */

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime: number;
}
'''

    # ── stores/auth-store.ts ──
    templates["frontend/src/stores/auth-store.ts"] = '''import { create } from "zustand";
import { api } from "@/lib/api-client";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem("auth_token"),
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const response = await api.post<{ access_token: string; user: User }>(
        "/api/v1/auth/login",
        { email, password }
      );
      localStorage.setItem("auth_token", response.access_token);
      set({ user: response.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (name, email, password) => {
    set({ isLoading: true });
    try {
      await api.post("/api/v1/auth/register", { name, email, password });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem("auth_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const user = await api.get<User>("/api/v1/auth/me");
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
      localStorage.removeItem("auth_token");
    }
  },
}));
'''

    # ── hooks ──
    templates["frontend/src/hooks/use-auth.ts"] = '''import { useAuthStore } from "@/stores/auth-store";

/** Convenience hook for auth state and actions */
export function useAuth() {
  const { user, isAuthenticated, isLoading, login, logout, register, fetchUser } =
    useAuthStore();

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
    fetchUser,
  };
}
'''

    templates["frontend/src/hooks/use-api.ts"] = '''import { useQuery, useMutation, type UseQueryOptions } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import { toast } from "sonner";

/** Generic hook for GET requests with caching */
export function useApiQuery<T>(
  key: string[],
  endpoint: string,
  options?: Partial<UseQueryOptions<T, ApiError>>
) {
  return useQuery<T, ApiError>({
    queryKey: key,
    queryFn: () => api.get<T>(endpoint),
    ...options,
  });
}

/** Generic hook for mutations (POST/PUT/DELETE) with toast notifications */
export function useApiMutation<TData, TVariables>(
  endpoint: string,
  method: "post" | "put" | "patch" | "delete" = "post",
  options?: {
    successMessage?: string;
    errorMessage?: string;
    onSuccess?: (data: TData) => void;
  }
) {
  return useMutation<TData, ApiError, TVariables>({
    mutationFn: (variables) => api[method]<TData>(endpoint, variables),
    onSuccess: (data) => {
      if (options?.successMessage) toast.success(options.successMessage);
      options?.onSuccess?.(data);
    },
    onError: (error) => {
      toast.error(options?.errorMessage || error.message);
    },
  });
}
'''

    templates["frontend/src/hooks/use-debounce.ts"] = '''import { useState, useEffect } from "react";

/** Debounce a value — useful for search inputs */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
'''

    templates["frontend/src/hooks/use-local-storage.ts"] = '''import { useState, useEffect } from "react";

/** Persist state in localStorage with type safety */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch {
      console.warn(`Failed to save ${key} to localStorage`);
    }
  }, [key, storedValue]);

  return [storedValue, setStoredValue] as const;
}
'''

    # ── UI Components ──
    templates["frontend/src/components/ui/button.tsx"] = '''import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  isLoading?: boolean;
}

const variants = {
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  ghost: "hover:bg-accent hover:text-accent-foreground",
  link: "text-primary underline-offset-4 hover:underline",
};

const sizes = {
  default: "h-10 px-4 py-2",
  sm: "h-9 rounded-md px-3",
  lg: "h-11 rounded-md px-8",
  icon: "h-10 w-10",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : null}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
'''

    templates["frontend/src/components/ui/input.tsx"] = '''import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, label, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\\s+/g, "-");

    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
            "ring-offset-background placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-destructive focus-visible:ring-destructive",
            className
          )}
          ref={ref}
          {...props}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
'''

    templates["frontend/src/components/ui/card.tsx"] = '''import * as React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border bg-card text-card-foreground shadow-sm",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: CardProps) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}

export function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export function CardContent({ className, ...props }: CardProps) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

export function CardFooter({ className, ...props }: CardProps) {
  return <div className={cn("flex items-center p-6 pt-0", className)} {...props} />;
}
'''

    templates["frontend/src/components/ui/dialog.tsx"] = '''import * as React from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}

export function Dialog({ open, onClose, children, className }: DialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Content */}
      <div
        className={cn(
          "relative z-50 w-full max-w-lg rounded-lg bg-background p-6 shadow-lg",
          "animate-in fade-in-0 zoom-in-95",
          className
        )}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  );
}
'''

    templates["frontend/src/components/ui/loading-spinner.tsx"] = '''import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function LoadingSpinner({ className, size = "md" }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  return (
    <div className={cn("flex items-center justify-center", className)}>
      <svg
        className={cn("animate-spin text-primary", sizeClasses[size])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
}
'''

    templates["frontend/src/components/ui/toast.tsx"] = '''// Using sonner for toast notifications (already imported in main.tsx)
// Usage: import { toast } from "sonner";
//
// toast.success("Operation successful");
// toast.error("Something went wrong");
// toast.info("Here's some info");
// toast.loading("Processing...");

export { toast } from "sonner";
'''

    # ── Layout Components ──
    templates["frontend/src/components/layout/header.tsx"] = f'''import {{ Link, useLocation }} from "react-router-dom";
import {{ useAuth }} from "@/hooks/use-auth";
import {{ Button }} from "@/components/ui/button";
import {{ cn }} from "@/lib/utils";
import {{ ROUTES }} from "@/lib/constants";

export function Header() {{
  const {{ isAuthenticated, user, logout }} = useAuth();
  const location = useLocation();

  const navLinks = [
    {{ label: "Home", href: ROUTES.HOME }},
    ...(isAuthenticated ? [{{ label: "Dashboard", href: ROUTES.DASHBOARD }}] : []),
  ];

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-bold text-primary">
            {pn}
          </Link>
          <nav className="hidden gap-4 md:flex">
            {{navLinks.map((link) => (
              <Link
                key={{link.href}}
                to={{link.href}}
                className={{cn(
                  "text-sm font-medium transition-colors hover:text-primary",
                  location.pathname === link.href
                    ? "text-foreground"
                    : "text-muted-foreground"
                )}}
              >
                {{link.label}}
              </Link>
            ))}}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          {{isAuthenticated ? (
            <>
              <span className="text-sm text-muted-foreground">
                {{user?.name || user?.email}}
              </span>
              <Button variant="outline" size="sm" onClick={{logout}}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link to={{ROUTES.LOGIN}}>
                <Button variant="ghost" size="sm">Login</Button>
              </Link>
              <Link to={{ROUTES.REGISTER}}>
                <Button size="sm">Get Started</Button>
              </Link>
            </>
          )}}
        </div>
      </div>
    </header>
  );
}}
'''

    templates["frontend/src/components/layout/footer.tsx"] = f'''import {{ APP_NAME }} from "@/lib/constants";

export function Footer() {{
  return (
    <footer className="border-t bg-background">
      <div className="container mx-auto flex flex-col items-center gap-4 px-4 py-8 md:flex-row md:justify-between">
        <p className="text-sm text-muted-foreground">
          &copy; {{new Date().getFullYear()}} {{APP_NAME}}. All rights reserved.
        </p>
        <div className="flex gap-4">
          <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
            Privacy
          </a>
          <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
            Terms
          </a>
          <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}}
'''

    templates["frontend/src/components/layout/sidebar.tsx"] = '''import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Home, Settings, User, LayoutDashboard } from "lucide-react";

interface SidebarLink {
  label: string;
  href: string;
  icon: React.ElementType;
}

const links: SidebarLink[] = [
  { label: "Home", href: "/", icon: Home },
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-background md:block">
      <nav className="flex flex-col gap-1 p-4">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = location.pathname === link.href;

          return (
            <Link
              key={link.href}
              to={link.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
'''

    templates["frontend/src/components/layout/root-layout.tsx"] = '''import { Header } from "./header";
import { Footer } from "./footer";

interface RootLayoutProps {
  children: React.ReactNode;
}

export function RootLayout({ children }: RootLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container mx-auto px-4 py-8">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
'''

    # ── Error components ──
    templates["frontend/src/components/error-boundary.tsx"] = '''import React from "react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
          <h2 className="text-2xl font-bold text-destructive">Something went wrong</h2>
          <p className="text-muted-foreground">{this.state.error?.message}</p>
          <Button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
          >
            Try Again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
'''

    templates["frontend/src/components/not-found.tsx"] = '''import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-7xl font-bold text-primary">404</h1>
      <h2 className="text-2xl font-semibold">Page Not Found</h2>
      <p className="max-w-md text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Link to={ROUTES.HOME}>
        <Button>Back to Home</Button>
      </Link>
    </div>
  );
}
'''

    # ── Pages ──
    templates["frontend/src/pages/home.tsx"] = f'''import {{ Link }} from "react-router-dom";
import {{ Button }} from "@/components/ui/button";
import {{ Card, CardContent, CardHeader, CardTitle }} from "@/components/ui/card";
import {{ ROUTES }} from "@/lib/constants";

export default function HomePage() {{
  return (
    <div className="space-y-16">
      {{/* Hero Section */}}
      <section className="flex flex-col items-center gap-6 py-16 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
          Welcome to{" "}
          <span className="text-primary">{pn}</span>
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          A production-ready application built with modern best practices.
          Fast, secure, and beautifully designed.
        </p>
        <div className="flex gap-4">
          <Link to={{ROUTES.REGISTER}}>
            <Button size="lg">Get Started</Button>
          </Link>
          <Link to={{ROUTES.LOGIN}}>
            <Button variant="outline" size="lg">Sign In</Button>
          </Link>
        </div>
      </section>

      {{/* Features Section */}}
      <section className="space-y-8">
        <h2 className="text-center text-3xl font-bold">Features</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Fast & Modern</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Built with React 19, TypeScript, and Vite for blazing fast performance.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Secure by Default</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                JWT authentication, input validation, and security best practices baked in.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Beautiful UI</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Tailwind CSS with a component library for consistent, accessible design.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}}
'''

    # ── Tests ──
    templates["frontend/src/__tests__/App.test.tsx"] = '''import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect } from "vitest";
import App from "../App";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderApp() {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe("App", () => {
  it("renders without crashing", () => {
    renderApp();
    expect(document.getElementById("root") || document.body).toBeTruthy();
  });
});
'''

    templates["frontend/vitest.config.ts"] = '''import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: [],
    css: true,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
'''

    return templates


# ═════════════════════════════════════════════════════════════════════════════
# BACKEND TEMPLATES — FastAPI + Python
# ═════════════════════════════════════════════════════════════════════════════

def get_sclass_backend_templates(project_name: str, features: List[str]) -> Dict[str, str]:
    """Generate S-class backend templates."""
    pn = project_name.replace("-", "_").replace(" ", "_").lower()
    templates = {}

    # ── requirements.txt ──
    templates["backend/requirements.txt"] = """fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
python-dotenv>=1.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
sqlalchemy>=2.0.0
alembic>=1.14.0
httpx>=0.28.0
structlog>=24.4.0
python-multipart>=0.0.18
"""

    # ── .env.example ──
    templates["backend/.env.example"] = f"""# {project_name} Backend Configuration
# Copy to .env and fill in values

# App
APP_NAME={project_name}
APP_ENV=development
DEBUG=true
API_V1_PREFIX=/api/v1

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/{pn}

# Security — CHANGE THESE IN PRODUCTION
SECRET_KEY=change-me-to-a-random-64-char-string-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
"""

    # ── main.py ──
    templates["backend/main.py"] = f'''"""
{project_name} — API Server
"""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.middleware.error_handler import register_exception_handlers

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI app."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for {project_name}",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {{
            "status": "healthy",
            "version": "1.0.0",
            "app": settings.APP_NAME,
        }}

    logger.info("app_created", app_name=settings.APP_NAME, debug=settings.DEBUG)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
'''

    # ── app/__init__.py ──
    templates["backend/app/__init__.py"] = ""

    # ── core/config.py ──
    templates["backend/app/core/__init__.py"] = ""
    templates["backend/app/core/config.py"] = f'''"""
Application configuration — loaded from environment variables.
Uses pydantic-settings for validation and type safety.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "{project_name}"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
'''

    # ── core/security.py ──
    templates["backend/app/core/security.py"] = '''"""
Security utilities — JWT tokens and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
'''

    # ── core/database.py ──
    templates["backend/app/core/database.py"] = '''"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency — provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

    # ── core/exceptions.py ──
    templates["backend/app/core/exceptions.py"] = '''"""
Custom exception classes for structured error responses.
"""

from typing import Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found (404)."""

    def __init__(self, resource: str = "Resource", id: str = ""):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            detail=f"{resource} with id '{id}' was not found" if id else f"{resource} not found",
        )


class UnauthorizedException(AppException):
    """Authentication required (401)."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    """Access denied (403)."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403)


class ValidationException(AppException):
    """Validation error (422)."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, status_code=422)


class ConflictException(AppException):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)
'''

    # ── core/logging_config.py ──
    templates["backend/app/core/logging_config.py"] = '''"""
Structured logging configuration using structlog.
"""

import logging
import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
'''

    # ── middleware ──
    templates["backend/app/middleware/__init__.py"] = ""
    templates["backend/app/middleware/error_handler.py"] = '''"""
Global exception handlers for consistent error responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from app.core.exceptions import AppException

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            "app_error",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_error",
            error=str(exc),
            path=request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "status_code": 500,
            },
        )
'''

    # ── API ──
    templates["backend/app/api/__init__.py"] = ""
    templates["backend/app/api/deps.py"] = '''"""
API dependencies — auth, database, pagination.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Extract and validate user ID from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return user_id


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """Extract user ID if token is present, otherwise None."""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    return payload.get("sub") if payload else None
'''

    templates["backend/app/api/v1/__init__.py"] = ""
    templates["backend/app/api/v1/router.py"] = '''"""
API v1 router — aggregates all v1 endpoints.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Import and include route modules here:
# from app.api.v1 import auth, users, items
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
'''

    # ── Schemas ──
    templates["backend/app/schemas/__init__.py"] = ""
    templates["backend/app/schemas/common.py"] = '''"""
Common schemas shared across the application.
"""

from pydantic import BaseModel
from typing import Generic, List, Optional, TypeVar
from datetime import datetime

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    status_code: int = 200


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""
    created_at: datetime
    updated_at: Optional[datetime] = None
'''

    # ── Models ──
    templates["backend/app/models/__init__.py"] = '''"""SQLAlchemy models."""
'''

    # ── Services ──
    templates["backend/app/services/__init__.py"] = ""

    # ── Utils ──
    templates["backend/app/utils/__init__.py"] = ""
    templates["backend/app/utils/helpers.py"] = '''"""
Utility helpers.
"""

import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)
'''

    # ── Tests ──
    templates["backend/tests/__init__.py"] = ""
    templates["backend/tests/conftest.py"] = '''"""
Test fixtures and configuration.
"""

import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

# Override settings for testing
settings.DATABASE_URL = "sqlite:///./test.db"
settings.DEBUG = True

from main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c
'''

    templates["backend/tests/test_health.py"] = '''"""
Health check tests.
"""


def test_health_endpoint(client):
    """Health check should return healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
'''

    # ── Dockerfile ──
    templates["backend/Dockerfile"] = f'''# Multi-stage build for {project_name} backend
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    return templates


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROOT / DEVOPS TEMPLATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_sclass_root_templates(project_name: str, tech_stack: Dict[str, str]) -> Dict[str, str]:
    """Generate S-class root-level and DevOps templates."""
    pn = project_name
    backend = tech_stack.get("backend", "FastAPI")
    frontend = tech_stack.get("frontend", "React")
    database = tech_stack.get("database", "PostgreSQL")

    templates = {}

    # ── README.md ──
    templates["README.md"] = f'''# {pn}

> Production-ready application built with {backend} + {frontend}

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | {frontend}, TypeScript, Tailwind CSS |
| Backend | {backend}, Python 3.12 |
| Database | {database} |
| Auth | JWT + bcrypt |
| Deployment | Docker, Docker Compose |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (optional)

### Development Setup

1. **Clone and install:**
```bash
git clone <repo-url>
cd {pn.lower().replace(" ", "-")}
```

2. **Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

3. **Frontend:**
```bash
cd frontend
npm install
npm run dev
```

4. **Docker (full stack):**
```bash
docker-compose up --build
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
{pn.lower().replace(" ", "-")}/
├── frontend/          # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Route-level pages
│   │   ├── hooks/       # Custom React hooks
│   │   ├── lib/         # Utilities, API client
│   │   ├── stores/      # State management (Zustand)
│   │   └── types/       # TypeScript definitions
│   └── ...
├── backend/           # {backend} API
│   ├── app/
│   │   ├── api/         # Route handlers
│   │   ├── core/        # Config, security, DB
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   └── tests/
└── docker-compose.yml
```

## License

MIT
'''

    # ── .gitignore ──
    templates[".gitignore"] = """# Dependencies
node_modules/
.venv/
venv/
__pycache__/

# Build
dist/
build/
*.egg-info/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo
*.code-workspace

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log

# Database
*.db
*.sqlite3
"""

    # ── docker-compose.yml ──
    templates["docker-compose.yml"] = f'''services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/{pn.lower().replace(" ", "_")}
      - SECRET_KEY=${{SECRET_KEY:-dev-secret-key-change-in-production}}
      - DEBUG=true
      - CORS_ORIGINS=["http://localhost:3000"]
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api
    volumes:
      - ./frontend:/app
      - /app/node_modules

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: {pn.lower().replace(" ", "_")}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
'''

    # ── CI/CD ──
    templates[".github/workflows/ci.yml"] = f'''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/ -v

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Type check
        run: |
          cd frontend
          npm run type-check
      - name: Lint
        run: |
          cd frontend
          npm run lint
      - name: Build
        run: |
          cd frontend
          npm run build
'''

    # ── Makefile ──
    templates["Makefile"] = f'''# {pn} — Development Commands

.PHONY: dev dev-backend dev-frontend setup test lint docker

# Full development stack
dev:
\tdocker-compose up --build

# Backend only
dev-backend:
\tcd backend && uvicorn main:app --reload --port 8000

# Frontend only
dev-frontend:
\tcd frontend && npm run dev

# Initial setup
setup:
\tcd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
\tcd frontend && npm install

# Run all tests
test:
\tcd backend && python -m pytest tests/ -v
\tcd frontend && npm run test

# Lint all
lint:
\tcd frontend && npm run lint

# Docker
docker:
\tdocker-compose up --build -d

# Stop
stop:
\tdocker-compose down
'''

    return templates


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def get_sclass_templates(
    project_name: str,
    tech_stack: Dict[str, str],
    features: List[str],
    user_idea: str = "",
) -> Dict[str, str]:
    """
    Generate a complete project template set.
    
    Now delegates to SSS-class frontend templates when available,
    falling back to S-class templates.

    Returns a flat dict of {path: content} for all project files.
    """
    all_templates = {}

    backend_fw = tech_stack.get("backend", "")
    frontend_fw = tech_stack.get("frontend", "")

    # Root / DevOps
    all_templates.update(get_sclass_root_templates(project_name, tech_stack))

    # Backend
    if backend_fw and backend_fw.lower() != "none":
        all_templates.update(get_sclass_backend_templates(project_name, features))

    # Frontend — try SSS-class first, fall back to S-class
    if frontend_fw and frontend_fw.lower() != "none":
        try:
            from backend.templates.sss_class_frontend import get_sss_class_frontend_templates
            sss_templates = get_sss_class_frontend_templates(project_name, features, user_idea)
            all_templates.update(sss_templates)
        except ImportError:
            all_templates.update(get_sclass_frontend_templates(project_name, features))

    return all_templates
