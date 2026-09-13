import { notifyUnauthorized } from "./session";

const API_BASE = "/api";

/** Thrown by apiFetch on any non-2xx response. `body` is the parsed JSON error body, if any. */
export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  /** Plain objects are JSON-encoded automatically; pass FormData as-is (e.g. OTA upload in a later ticket). */
  body?: unknown;
  /**
   * Set true for calls whose own 401 is expected and handled inline by the
   * caller (e.g. the login form submitting a wrong password) rather than
   * meaning "the session died, go back to the login screen".
   */
  skipAuthRedirect?: boolean;
}

/**
 * Shared fetch wrapper — every REST call this app makes should go through
 * this, not raw `fetch`. Reused starting with this ticket by FE-2..FE-5.
 *
 * - Always sends the session cookie (`credentials: "include"`), per
 *   INTERFACES.md §12.1.
 * - JSON-encodes plain object `body`s; passes `FormData` through untouched.
 * - On a 401 from a non-auth-flow call, notifies subscribers (see
 *   lib/session.ts) so the app can drop back to the login screen instead of
 *   failing silently or looping.
 * - Throws `ApiError` (with `status`/`body`) on any non-2xx response.
 *
 * Usage:
 *   const devices = await apiFetch<Device[]>("/devices");
 *   await apiFetch("/devices/foo/commands", { method: "POST", body: { command: "relay1", value: true } });
 */
export async function apiFetch<T = unknown>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, skipAuthRedirect, headers, ...rest } = options;
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      ...(body !== undefined && !isFormData ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : isFormData ? (body as FormData) : JSON.stringify(body),
  });

  if (response.status === 401 && !skipAuthRedirect) {
    notifyUnauthorized();
  }

  if (!response.ok) {
    let parsedBody: unknown;
    try {
      parsedBody = await response.json();
    } catch {
      // no/invalid JSON error body — leave undefined
    }
    throw new ApiError(response.status, `${options.method ?? "GET"} ${path} failed with ${response.status}`, parsedBody);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return undefined as T;
}
