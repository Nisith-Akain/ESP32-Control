import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch, ApiError } from "./api";
import { onUnauthorized } from "./session";
import { apiSocket } from "./ws";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthState {
  /** "loading" while the initial GET /api/auth/status check is in flight. */
  status: AuthStatus;
  /** Inline error message for the login form (e.g. wrong password); null otherwise. */
  error: string | null;
  login: (password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

/**
 * Owns the app's login-gate state (INTERFACES.md §12.1). Wrap the whole app
 * in this once (see main.tsx); read state anywhere via useAuth().
 *
 * Also subscribes to lib/session.ts's onUnauthorized() so any 401 surfaced
 * by apiFetch, or a policy-violation close from the WS client, drops the
 * app back to the login screen automatically.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<{ authenticated: boolean }>("/auth/status", { skipAuthRedirect: true })
      .then((result) => {
        if (!cancelled) {
          setStatus(result.authenticated ? "authenticated" : "unauthenticated");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("unauthenticated");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(
    () =>
      onUnauthorized(() => {
        apiSocket.disconnect();
        setStatus("unauthenticated");
      }),
    []
  );

  const login = useCallback(async (password: string) => {
    setError(null);
    try {
      await apiFetch("/auth/login", { method: "POST", body: { password }, skipAuthRedirect: true });
      setStatus("authenticated");
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? "Incorrect password." : "Login failed. Please try again.");
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST", skipAuthRedirect: true });
    } finally {
      apiSocket.disconnect();
      setStatus("unauthenticated");
    }
  }, []);

  return <AuthContext.Provider value={{ status, error, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
