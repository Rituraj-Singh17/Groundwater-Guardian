export default function StatusBadge({ value }) {
  const text = value == null || value === "" ? "Unknown" : String(value).replaceAll("_", " ");
  const normalized = text.toLowerCase();
  let tone = "neutral";
  if (["resolved", "high", "good", "reliable", "healthy"].includes(normalized)) tone = "success";
  else if (["open", "critical", "poor", "low", "high priority"].includes(normalized)) tone = "danger";
  else if (["investigating", "medium", "moderate", "needs review"].includes(normalized)) tone = "warning";
  return <span className={`status-badge ${tone}`}><i />{text}</span>;
}