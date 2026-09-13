import { notifyUnauthorized } from "./session";

/** Mirrors INTERFACES.md §3 — server -> client push message shapes. */
export type WSMessage =
  | { type: "telemetry"; device_id: string; ts: string; data: Record<string, number | string | boolean> }
  | { type: "status"; device_id: string; status: "online" | "offline"; last_heartbeat: string }
  | { type: "command_ack"; device_id: string; command_id: string; status: "pending" | "sent" | "acked" | "failed" }
  | { type: "automation_triggered"; automation_id: string; device_id: string; command_id: string };

/** Mirrors INTERFACES.md §3 — client -> server subscribe request shapes. */
export type WSSubscription = { channel: "devices" } | { channel: "device"; device_id: string };

type MessageHandler = (message: WSMessage) => void;

const RECONNECT_DELAY_MS = 2000;

/**
 * Thin wrapper around the single shared `/ws` connection (INTERFACES.md §3).
 * Same-origin, so the browser attaches the session cookie automatically on
 * the upgrade request — no extra credential handling needed here.
 *
 * Reused starting with this ticket by FE-2 (`devices` channel) and FE-3
 * (`device` channel). Usage from a page/hook:
 *
 *   apiSocket.connect();
 *   apiSocket.subscribe({ channel: "devices" });
 *   const unsubscribe = apiSocket.onMessage((msg) => { ... });
 *   // on unmount: unsubscribe();
 *   // apiSocket.disconnect() is optional — safe to leave connected for other pages.
 *
 * On a 401-equivalent handshake rejection (server closes with policy
 * violation, code 1008, per INTERFACES.md §3/§12.1) this notifies the same
 * "session died" listeners as lib/api.ts instead of silently retrying.
 */
export class ApiSocket {
  private socket: WebSocket | null = null;
  private handlers = new Set<MessageHandler>();
  private subscriptions: WSSubscription[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private explicitlyClosed = false;

  private get url(): string {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${window.location.host}/ws`;
  }

  /** Opens the connection if not already open/opening. Safe to call repeatedly/redundantly. */
  connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this.explicitlyClosed = false;
    this.clearReconnectTimer();

    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.addEventListener("open", () => {
      this.subscriptions.forEach((subscription) => this.send(subscription));
    });

    socket.addEventListener("message", (event) => {
      let parsed: WSMessage;
      try {
        parsed = JSON.parse(event.data as string) as WSMessage;
      } catch {
        return; // ignore malformed frames
      }
      this.handlers.forEach((handler) => handler(parsed));
    });

    socket.addEventListener("close", (event) => {
      if (event.code === 1008) {
        notifyUnauthorized();
        return; // don't reconnect a rejected/unauthenticated handshake
      }
      if (!this.explicitlyClosed) {
        this.scheduleReconnect();
      }
    });

    // "close" always follows "error" for a failed connection attempt;
    // reconnect scheduling lives in the close handler so it isn't duplicated.
    socket.addEventListener("error", () => undefined);
  }

  /** Sends a subscribe frame now (if connected) and remembers it so reconnects re-subscribe. */
  subscribe(subscription: WSSubscription): void {
    const alreadyTracked = this.subscriptions.some((s) => JSON.stringify(s) === JSON.stringify(subscription));
    if (!alreadyTracked) {
      this.subscriptions.push(subscription);
    }
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.send(subscription);
    }
  }

  /** Registers a handler for every incoming push message. Returns an unsubscribe function. */
  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  /** Closes the connection, stops auto-reconnect, and forgets remembered subscriptions. */
  disconnect(): void {
    this.explicitlyClosed = true;
    this.clearReconnectTimer();
    this.subscriptions = [];
    this.socket?.close();
    this.socket = null;
  }

  private send(subscription: WSSubscription): void {
    this.socket?.send(JSON.stringify({ type: "subscribe", ...subscription }));
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => this.connect(), RECONNECT_DELAY_MS);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

/** Single shared instance — import and use this rather than constructing your own. */
export const apiSocket = new ApiSocket();
