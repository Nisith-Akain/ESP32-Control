// Minimal stand-in for BE-1's /api/auth/* + generic 401 behavior, for
// manually exercising FE-1's login gate before BE-1 is running/qa-passed.
// Not part of the shipped frontend build; not a substitute for BE-1's tests.
//
// Usage:
//   node mock-server/server.mjs
//   (in another terminal) npm run dev   -- vite.config.ts proxies /api and
//   /ws to http://localhost:8000 by default, which is what this listens on.
//
// Covers, per TEAM/INTERFACES.md §12.1:
//   GET  /api/auth/status  -> { authenticated }
//   POST /api/auth/login   -> { status: "ok" } + Set-Cookie, or 401
//   POST /api/auth/logout  -> { status: "ok" }, clears cookie
//   any other /api/*       -> 401 { error: "unauthenticated" } without a
//                             valid session cookie (so the redirect-to-login
//                             behavior in lib/api.ts can be exercised),
//                             otherwise a trivial 200 stub payload.
//   /ws                     -> accepts the upgrade only with a valid session
//                             cookie; otherwise destroys the socket (close
//                             code 1008 isn't achievable with raw sockets, so
//                             this mock just refuses the handshake outright
//                             -- good enough for manual smoke-testing the
//                             "redirect on rejected handshake" path; BE-2
//                             owns the real 1008 behavior).

import http from "node:http";
import crypto from "node:crypto";

const PORT = process.env.MOCK_PORT ? Number(process.env.MOCK_PORT) : 8000;
const UI_PASSWORD = process.env.MOCK_UI_PASSWORD ?? "test";
const COOKIE_NAME = "session_token";

/** token -> expiry epoch ms */
const sessions = new Map();
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000;

function parseCookies(header) {
  const out = {};
  (header ?? "").split(";").forEach((pair) => {
    const idx = pair.indexOf("=");
    if (idx === -1) return;
    out[pair.slice(0, idx).trim()] = decodeURIComponent(pair.slice(idx + 1).trim());
  });
  return out;
}

function isValidSession(req) {
  const token = parseCookies(req.headers.cookie)[COOKIE_NAME];
  if (!token) return false;
  const expiry = sessions.get(token);
  if (!expiry || expiry < Date.now()) {
    sessions.delete(token);
    return false;
  }
  return true;
}

function sendJson(res, status, body, extraHeaders = {}) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload), ...extraHeaders });
  res.end(payload);
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk) => (raw += chunk));
    req.on("end", () => {
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");

  if (req.method === "GET" && url.pathname === "/api/auth/status") {
    return sendJson(res, 200, { authenticated: isValidSession(req) });
  }

  if (req.method === "POST" && url.pathname === "/api/auth/login") {
    let body;
    try {
      body = await readJsonBody(req);
    } catch {
      return sendJson(res, 400, { error: "invalid_json" });
    }
    if (body.password !== UI_PASSWORD) {
      return sendJson(res, 401, { error: "invalid_password" });
    }
    const token = crypto.randomBytes(32).toString("hex");
    sessions.set(token, Date.now() + SESSION_TTL_MS);
    return sendJson(res, 200, { status: "ok" }, {
      "Set-Cookie": `${COOKIE_NAME}=${token}; HttpOnly; SameSite=Lax; Path=/`,
    });
  }

  if (req.method === "POST" && url.pathname === "/api/auth/logout") {
    const token = parseCookies(req.headers.cookie)[COOKIE_NAME];
    if (token) sessions.delete(token);
    return sendJson(res, 200, { status: "ok" }, {
      "Set-Cookie": `${COOKIE_NAME}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0`,
    });
  }

  if (url.pathname.startsWith("/api/")) {
    if (!isValidSession(req)) {
      return sendJson(res, 401, { error: "unauthenticated" });
    }
    // Trivial stub payloads so other pages don't hard-crash if pointed here
    // manually; real shapes are BE-1/BE-2/etc's contract, not this mock's job.
    if (url.pathname === "/api/devices") {
      return sendJson(res, 200, []);
    }
    return sendJson(res, 200, {});
  }

  sendJson(res, 404, { error: "not_found" });
});

server.on("upgrade", (req, socket) => {
  if (req.url !== "/ws" || !isValidSession(req)) {
    socket.destroy();
    return;
  }
  const acceptKey = req.headers["sec-websocket-key"];
  const acceptHash = crypto
    .createHash("sha1")
    .update(acceptKey + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    .digest("base64");
  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      `Sec-WebSocket-Accept: ${acceptHash}\r\n\r\n`
  );
  // No message framing implemented — this mock only proves the handshake
  // succeeds/fails based on the session cookie, for manual testing of FE-1's
  // login gate. BE-2 owns the real subscribe/push protocol.
});

server.listen(PORT, () => {
  console.log(`Mock auth server listening on http://localhost:${PORT}`);
  console.log(`UI_PASSWORD (mock) = "${UI_PASSWORD}" (override with MOCK_UI_PASSWORD env var)`);
});
