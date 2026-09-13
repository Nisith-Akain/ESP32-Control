import { NavLink } from "react-router-dom";
import "./Sidebar.css";

/** Binding nav structure per the ticket — exactly these four sections. */
const NAV_ITEMS = [
  { to: "/devices", label: "Devices" },
  { to: "/automations", label: "Automations" },
  { to: "/logs", label: "Logs" },
  { to: "/agents", label: "Agents" },
];

interface SidebarProps {
  open: boolean;
  onNavigate: () => void;
}

/** Left sidebar. On narrow viewports it's an off-canvas drawer toggled from NavBar; see Sidebar.css. */
export default function Sidebar({ open, onNavigate }: SidebarProps) {
  return (
    <nav className={`sidebar ${open ? "sidebar--open" : ""}`} aria-label="Primary">
      <ul className="sidebar__list">
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              className={({ isActive }) => `sidebar__link ${isActive ? "sidebar__link--active" : ""}`}
              onClick={onNavigate}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
