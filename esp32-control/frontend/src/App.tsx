import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./lib/auth";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DevicesPage from "./pages/DevicesPage";
import AutomationsPage from "./pages/AutomationsPage";
import LogsPage from "./pages/LogsPage";
import AgentsPage from "./pages/AgentsPage";

/**
 * Login gate (INTERFACES.md §12.1): while the initial auth check is
 * pending, show nothing but a loading state; if unauthenticated, render only
 * the login screen (no app shell/routes at all); once authenticated, render
 * the real app shell + router.
 */
export default function App() {
  const { status } = useAuth();

  if (status === "loading") {
    return (
      <div className="app-loading" role="status">
        Loading&#8230;
      </div>
    );
  }

  if (status === "unauthenticated") {
    return <LoginPage />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/devices" replace />} />
        <Route path="/devices" element={<DevicesPage />} />
        <Route path="/automations" element={<AutomationsPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="*" element={<Navigate to="/devices" replace />} />
      </Routes>
    </Layout>
  );
}
