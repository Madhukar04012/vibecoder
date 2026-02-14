import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  login as apiLogin,
  signup as apiSignup,
  type LoginRequest,
  type SignupRequest,
} from "@/api/auth";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());

  useEffect(() => {
    if (token) {
      setStoredToken(token);
    } else {
      clearStoredToken();
    }
  }, [token]);

  const login = useCallback(async (data: LoginRequest) => {
    const res = await apiLogin(data);
    setToken(res.access_token);
  }, []);

  const signup = useCallback(async (data: SignupRequest) => {
    await apiSignup(data);
    // Auto-login after signup; surface errors to caller
    const res = await apiLogin({ email: data.email, password: data.password });
    setToken(res.access_token);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    clearStoredToken();
  }, []);

  const value: AuthContextType = {
    token,
    isAuthenticated: !!token,
    login,
    signup,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
