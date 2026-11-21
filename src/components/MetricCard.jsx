import { ArrowUpRight } from "lucide-react";

export default function MetricCard({ label, value, hint, icon: Icon, tone = "green" }) {
  return (
    <article className="metric-card">
      <div className="metric-top"><span>{label}</span><div className={`metric-icon ${tone}`}>{Icon && <Icon size={19} />}</div></div>
      <div className="metric-value">{value ?? "—"}</div>
      <div className="metric-hint">{hint || "From the connected backend"} <ArrowUpRight size={13} /></div>
    </article>
  );
}