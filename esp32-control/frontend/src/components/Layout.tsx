import { useState, type ReactNode } from "react";
import NavBar from "./NavBar";
import Sidebar from "./Sidebar";
import "./Layout.css";

/** App shell used for every authenticated route: nav bar + collapsible sidebar + content area. */
export default function Layout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <NavBar onToggleSidebar={() => setSidebarOpen((open) => !open)} />
      <div className="app-shell__body">
        <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />
        <main className="app-shell__content">{children}</main>
      </div>
    </div>
  );
}
