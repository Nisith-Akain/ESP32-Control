import { useState } from "react";
import { useAuth } from "../lib/auth";
import "./NavBar.css";

interface NavBarProps {
  onToggleSidebar: () => void;
}

/** Top nav bar: app title, mobile sidebar toggle, and the logout action (INTERFACES.md §12.1). */
export default function NavBar({ onToggleSidebar }: NavBarProps) {
  const { logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
    } finally {
      setLoggingOut(false);
    }
  };

  return (
    <header className="nav-bar">
      <button type="button" className="nav-bar__menu-button" aria-label="Toggle sidebar" onClick={onToggleSidebar}>
        <span aria-hidden="true">&#9776;</span>
      </button>
      <span className="nav-bar__title">ESP32 Control</span>
      <button type="button" className="nav-bar__logout" onClick={handleLogout} disabled={loggingOut}>
        {loggingOut ? "Logging out…" : "Log out"}
      </button>
    </header>
  );
}
