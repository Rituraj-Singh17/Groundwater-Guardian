import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Droplets, MapPinned, RefreshCw } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { getDashboardSummary, getAlerts, getErrorMessage, unwrapList } from "../services/api";
import MetricCard from "../components/MetricCard";
import StatusBadge from "../components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadState";

const COLORS = ["#43c6a5", "#e6b85c", "#e47d6d", "#718c91"];
const first = (obj, keys) => {
  for (const key of keys) if (obj?.[key] !== undefined && obj?.[key] !== null) return obj[key];
  return undefined;
};
const fmt = (v) => v === undefined ? "—" : Number(v).toLocaleString();

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const [s, a] = await Promise.all([getDashboardSummary(), getAlerts({ page: 1, page_size: 5 })]);
      setSummary(s.data); setAlerts(unwrapList(a.data).slice(0, 5));
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const categories = first(summary, ["reliability_categories"]);
  const chartData = categories && typeof categories === "object"
    ? Object.entries(categories).map(([name, value]) => ({ name: name.replaceAll("_", " "), value: Number(value) })).filter(x => x.value > 0)
    : [];

  return (
    <div className="page-content">
      <div className="welcome-row"><div><div className="eyebrow">LIVE BACKEND SUMMARY</div><h2>Groundwater intelligence at a glance</h2><p>Understand data reliability, identify patterns and prioritize investigation.</p></div><button className="button secondary" onClick={load}><RefreshCw size={15}/> Refresh data</button></div>
      <div className="metric-grid">
        <MetricCard label="Monitoring stations" value={fmt(first(summary, ["total_stations"]))} hint="Stations in backend" icon={MapPinned}/>
        <MetricCard label="Observations" value={fmt(first(summary, ["total_observations"]))} hint="Processed readings" icon={Droplets} tone="blue"/>
        <MetricCard label="Total data alerts" value={fmt(first(summary, ["total_alerts"]))} hint="Detected patterns" icon={AlertTriangle} tone="amber"/>
        <MetricCard label="Open alerts" value={fmt(first(summary, ["open_alerts"]))} hint="Awaiting review" icon={Activity} tone="red"/>
      </div>
      <div className="dashboard-grid">
        <section className="panel chart-panel"><div className="panel-heading"><div><h3>Station reliability distribution</h3><p>Category counts returned by the API</p></div></div>
          {chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height={250}><PieChart><Pie data={chartData} dataKey="value" nameKey="name" innerRadius={68} outerRadius={96} paddingAngle={4}>{chartData.map((entry, i) => <Cell key={entry.name} fill={COLORS[i % COLORS.length]}/>)}</Pie><Tooltip contentStyle={{background:"#10221f",border:"1px solid #29413b",borderRadius:10,color:"#e8f2ee"}}/></PieChart></ResponsiveContainer><div className="chart-legend">{chartData.map((item,i)=><div key={item.name}><span style={{background:COLORS[i%COLORS.length]}}/>{item.name}<b>{item.value}</b></div>)}</div></div> : <EmptyState message="Reliability category counts are not present in the current summary response."/>}
        </section>
        <section className="panel"><div className="panel-heading"><div><h3>Maintenance overview</h3><p>Records currently tracked</p></div></div><div className="big-stat">{fmt(first(summary, ["maintenance_records"]))}</div><p className="muted">Maintenance records</p><div className="info-note"><Activity size={17}/><span>Use the Maintenance page to create or update investigation records.</span></div></section>
      </div>
      <section className="panel table-panel"><div className="panel-heading"><div><h3>Recent data-quality alerts</h3><p>Latest alerts returned by the backend</p></div><a className="text-link" href="/alerts">View all alerts →</a></div>
        {alerts.length ? <div className="table-scroll"><table><thead><tr><th>Alert</th><th>Station ID</th><th>Type</th><th>Severity</th><th>Status</th><th>Detected</th></tr></thead><tbody>{alerts.map((a,i)=><tr key={a.id ?? i}><td className="strong-cell">#{a.id ?? "—"}</td><td>{a.station_id ?? "—"}</td><td>{a.alert_type ?? "—"}</td><td><StatusBadge value={a.severity}/></td><td><StatusBadge value={a.status}/></td><td>{a.detected_at ? new Date(a.detected_at).toLocaleString() : "—"}</td></tr>)}</tbody></table></div> : <EmptyState message="No recent alerts were returned by the backend."/>}
      </section>
      <p className="domain-note">Important: A data-quality alert indicates a suspicious observation pattern. It does not confirm sensor or hardware failure.</p>
    </div>
  );
}