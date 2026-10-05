import { createContext } from "react";

import type { AuthStatus, AuthUser } from "./types";

export interface AuthContextValue {
  accessToken: string | null;
  status: AuthStatus;
  user: AuthUser | null;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  retrySession: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
