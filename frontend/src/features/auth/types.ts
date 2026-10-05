export type UserRole = "ADMIN" | "TEACHER";

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  institution_id: string;
}

export interface LoginResponse {
  access: string;
  user: AuthUser;
}

export interface RefreshResponse {
  access: string;
}

export type AuthStatus = "loading" | "anonymous" | "authenticated" | "error";
