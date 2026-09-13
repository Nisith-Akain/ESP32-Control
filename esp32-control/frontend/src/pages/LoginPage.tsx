import { useState, type FormEvent } from "react";
import { useAuth } from "../lib/auth";
import "./LoginPage.css";

/**
 * Single-password login screen per INTERFACES.md §12.1 — no username field,
 * checked server-side against UI_PASSWORD. Shown by App.tsx whenever
 * useAuth().status !== "authenticated".
 */
export default function LoginPage() {
  const { login, error } = useAuth();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!password || submitting) return;
    setSubmitting(true);
    try {
      await login(password);
    } catch {
      // Inline error is surfaced via useAuth().error; nothing else to do here.
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-page__form" onSubmit={handleSubmit}>
        <h1 className="login-page__title">ESP32 Control</h1>
        <label className="login-page__label" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          className="login-page__input"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoFocus
          autoComplete="current-password"
        />
        {error && (
          <p className="login-page__error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="login-page__submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
