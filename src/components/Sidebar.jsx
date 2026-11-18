import { NavLink } from "react-router-dom";
import { LayoutDashboard, MapPinned, BellRing, Wrench, Droplets, Activity } from "lucide-react";

const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/stations", label: "Stations", icon: MapPinned },
  { to: "/alerts", label: "Data alerts", icon: BellRing },
  { to: "/maintenance", label: "Maintenance", icon: Wrench }
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Droplets size={23} /></div>
        <div><strong>GROUNDWATER</strong><span>GUARDIAN</span></div>
      </div>
      <div className="side-label">WORKSPACE</div>
      <nav className="nav-links">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            <Icon size={18} /><span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="live-indicator"><span /> API connection is checked on load</div>
        <div className="side-foot"><Activity size={15} /> Groundwater monitoring</div>
      </div>
    </aside>
  );
}