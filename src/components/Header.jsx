import { Bell, Search } from "lucide-react";
import { useLocation } from "react-router-dom";

const titles = {
  "/": ["Overview", "Monitor station reliability and data-quality signals."],
  "/stations": ["Monitoring stations", "Explore stations and their reliability information."],
  "/alerts": ["Data-quality alerts", "Review suspicious observation patterns."],
  "/maintenance": ["Maintenance", "Track investigations and resolution work."]
};

export default function Header() {
  const location = useLocation();
  const [title, subtitle] = titles[location.pathname] || titles["/"];
  return (
    <header className="topbar">
      <div className="mobile-brand"> <span className="mobile-brand-icon">◈</span> Groundwater Guardian</div>
      <div className="page-heading"><div className="eyebrow">MONITORING WORKSPACE</div><h1>{title}</h1><p>{subtitle}</p></div>
      <div className="top-actions"><div className="system-pill"><span /> Monitoring system</div><button className="icon-button" aria-label="Notifications"><Bell size={18} /></button></div>
    </header>
  );
}