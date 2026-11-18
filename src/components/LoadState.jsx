import { RefreshCw } from "lucide-react";
export function LoadingState() { return <div className="state-box"><div className="spinner" /><p>Loading backend data…</p></div>; }
export function ErrorState({ message, onRetry }) {
  return <div className="state-box error-state"><strong>Unable to load data</strong><p>{message}</p><button className="button secondary" onClick={onRetry}><RefreshCw size={15}/> Retry</button></div>;
}
export function EmptyState({ message = "No records are available for this view." }) {
  return <div className="empty-state"><div className="empty-symbol">⌁</div><strong>Nothing to display yet</strong><p>{message}</p></div>;
}