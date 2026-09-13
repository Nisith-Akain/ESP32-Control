/**
 * Tiny pub/sub used to decouple "the session died" detection (in api.ts and
 * ws.ts) from "what the app should do about it" (AuthProvider, in auth.tsx).
 * Neither api.ts nor ws.ts import React, so this keeps them usable outside a
 * component tree too.
 */

type UnauthorizedListener = () => void;

let listeners: UnauthorizedListener[] = [];

/**
 * Register a callback to run whenever apiFetch() or the shared WebSocket
 * client (apiSocket) detects the current session is no longer valid — a 401
 * from a non-auth-flow endpoint, or a policy-violation close on the /ws
 * handshake (INTERFACES.md §12.1). AuthProvider is the expected subscriber;
 * returns an unsubscribe function.
 */
export function onUnauthorized(listener: UnauthorizedListener): () => void {
  listeners.push(listener);
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

/** Called internally by lib/api.ts and lib/ws.ts. Not for page code to call directly. */
export function notifyUnauthorized(): void {
  listeners.forEach((listener) => listener());
}
