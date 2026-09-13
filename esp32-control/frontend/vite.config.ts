import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api and /ws to the backend so the browser can use
// same-origin relative URLs (required for the session cookie in
// TEAM/INTERFACES.md §12.1 to be sent automatically on fetch/WS calls).
// Point BACKEND_ORIGIN at wherever BE-1/BE-2 is running locally, e.g.
//   BACKEND_ORIGIN=http://localhost:8000 npm run dev
// Until backend is available, `npm run mock:server` starts a minimal stand-in
// for /api/auth/* (+ generic 401 behavior) on this same default origin.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: BACKEND_ORIGIN,
        changeOrigin: true,
      },
      "/ws": {
        target: BACKEND_ORIGIN,
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
