import React from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import IntakePage from "../features/intake/IntakePage";
import DiscoveryPage from "../features/discovery/DiscoveryPage";
import DepositionPlanPage from "../features/deposition-plan/DepositionPlanPage";
import DepositionBattlegroundPage from "../features/deposition-battleground/DepositionBattlegroundPage";

const navItems = [
  { label: "Phase I", title: "Intake", to: "/" },
  { label: "Phase II", title: "Discovery", to: "/discovery" },
  { label: "Phase III", title: "Deposition Plan", to: "/deposition-plan" },
  { label: "Phase IV", title: "Deposition Battleground", to: "/deposition-battleground" }
];

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">CASECORE</div>
        <div className="brand-sub">Litigation OS · UI Workspace Shell</div>

        <div className="nav-group">
          <div className="nav-label">Workspaces</div>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `nav-link${isActive ? " active" : ""}`
              }
            >
              <div style={{ fontSize: 11, color: "#98a7c2", marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontWeight: 700 }}>{item.title}</div>
            </NavLink>
          ))}
        </div>

        <div className="nav-group">
          <div className="nav-label">Navigation Target</div>
          <div className="card">
            <h3>Current direction</h3>
            <p>
              Rebuild from the front of the litigation lifecycle using an action-first,
              war-room-oriented UI rather than dashboards or static documentation.
            </p>
          </div>
        </div>
      </aside>

      <main className="main">
        <Routes>
          <Route path="/" element={<IntakePage />} />
          <Route path="/discovery" element={<DiscoveryPage />} />
          <Route path="/deposition-plan" element={<DepositionPlanPage />} />
          <Route path="/deposition-battleground" element={<DepositionBattlegroundPage />} />
        </Routes>
      </main>
    </div>
  );
}
