/**
 * Auth API - Login and Signup
 */

import { apiFetch } from "@/lib/api";
import {
  getStoredToken as _getStoredToken,
  setStoredToken as _setStoredToken,
  clearStoredToken as _clearStoredToken,
} from "@/lib/auth-storage";

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

export const getStoredToken = _getStoredToken;
export const setStoredToken = _setStoredToken;
export const clearStoredToken = _clearStoredToken;

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
