import { useState } from "react";

import Coach from "./components/coach.jsx";
import Dashboard from "./components/dashboard.jsx";
import IngestBanner from "./components/IngestBanner.jsx";
import Openings from "./components/openings.jsx";
import StyleGap from "./components/stylegap.jsx";
import UsernameSetup from "./components/UsernameSetup.jsx";
import Weaknesses from "./components/weaknesses.jsx";
import { useUsername } from "./context/UsernameContext.jsx";
import "./App.css";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "ti-layout-dashboard" },
  { id: "openings", label: "Openings", icon: "ti-chess" },
  { id: "weaknesses", label: "Weaknesses", icon: "ti-report-analytics" },
  { id: "coach", label: "Coach", icon: "ti-message-circle" },
  { id: "style", label: "Style gap", icon: "ti-user-star" },
];

const PAGES = {
  dashboard: Dashboard,
  openings: Openings,
  weaknesses: Weaknesses,
  coach: Coach,
  style: StyleGap,
};

export default function App() {
  const { username, clearUsername } = useUsername();
  const [page, setPage] = useState("dashboard");
  const [refreshKey, setRefreshKey] = useState(0);

  if (!username) {
    return <UsernameSetup />;
  }

  const Page = PAGES[page];

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="logo">
          <div className="logo-name">Morphy</div>
          <div className="logo-sub">chess coach agent</div>
        </div>
        {NAV.map((n) => (
          <button
            key={n.id}
            className={`nav-item ${page === n.id ? "active" : ""}`}
            onClick={() => setPage(n.id)}
          >
            <i className={`ti ${n.icon}`} aria-hidden="true" />
            {n.label}
          </button>
        ))}
        <div className="sidebar-footer">
          <button type="button" className="user-pill" onClick={clearUsername} title="Change username">
            <div className="avatar">{username.slice(0, 2).toUpperCase()}</div>
            <div className="user-name">{username}</div>
          </button>
        </div>
      </nav>
      <main className="main">
        <IngestBanner username={username} onComplete={() => setRefreshKey((k) => k + 1)} />
        <Page username={username} refreshKey={refreshKey} />
      </main>
    </div>
  );
}
