/**
 * Auth API - Login and Signup
 */

import { apiFetch } from "@/lib/api";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
}

const TOKEN_KEY = "vibecober_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function signup(data: SignupRequest): Promise<UserResponse> {
  return apiFetch<UserResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getMe(): Promise<UserResponse> {
  return apiFetch<UserResponse>("/auth/me");
}
