import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import Stations from "./pages/Stations";
import Alerts from "./pages/Alerts";
import Maintenance from "./pages/Maintenance";

export default function App() {
  return <div className="app-shell"><Sidebar/><main className="main-area"><Header/><Routes><Route path="/" element={<Dashboard/>}/><Route path="/stations" element={<Stations/>}/><Route path="/alerts" element={<Alerts/>}/><Route path="/maintenance" element={<Maintenance/>}/></Routes><footer className="app-footer">GROUNDWATER GUARDIAN <span>•</span> Explainable monitoring-data reliability</footer></main></div>;
}