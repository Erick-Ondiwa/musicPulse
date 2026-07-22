import { useState } from "react";
import {
  Activity,
  Bot,
  ChartNoAxesCombined,
  Database,
  BookOpen,
  Menu,
  Music2,
  Radio,
  RefreshCw,
  Trophy,
  X,
} from "lucide-react";
import DashboardPage from "./pages/DashboardPage";
import RankingsPage from "./pages/RankingsPage";
import AssistantPage from "./pages/AssistantPage";
import IngestionPage from "./pages/IngestionPage";
import KnowledgePage from "./pages/KnowledgePage";

const navigation = [
  { id: "dashboard", label: "Dashboard", icon: ChartNoAxesCombined },
  { id: "rankings", label: "Rankings", icon: Trophy },
  { id: "assistant", label: "AI Assistant", icon: Bot },
  { id: "knowledge", label: "RAG Knowledge", icon: BookOpen },
  { id: "ingestion", label: "Data Ingestion", icon: Database },
];

const pageTitles = {
  dashboard: {
    eyebrow: "Music intelligence",
    title: "Dashboard",
    description: "Monitor releases, growth, artists, and current YouTube music activity.",
  },
  rankings: {
    eyebrow: "Performance analytics",
    title: "Music Rankings",
    description: "Explore trending, latest, and most-viewed songs from your database.",
  },
  assistant: {
    eyebrow: "Database-grounded AI",
    title: "Music Assistant",
    description: "Ask natural-language questions and receive answers supported by stored metrics.",
  },
  knowledge: {
    eyebrow: "Retrieval augmented generation",
    title: "RAG Knowledge Base",
    description: "Manage the evidence documents used for semantic retrieval and grounded answers.",
  },
  ingestion: {
    eyebrow: "Collection operations",
    title: "Data Ingestion",
    description: "Trigger YouTube collection jobs and monitor synchronization activity.",
  },
};

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [mobileOpen, setMobileOpen] = useState(false);
  const page = pageTitles[activePage];

  const changePage = (id) => {
    setActivePage(id);
    setMobileOpen(false);
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <Music2 size={24} />
          </div>
          <div>
            <strong>MusicPulse</strong>
            <span>AI Intelligence</span>
          </div>
        </div>

        <button
          className="sidebar-close"
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        >
          <X size={20} />
        </button>

        <nav className="nav-list">
          {navigation.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`nav-item ${activePage === id ? "active" : ""}`}
              onClick={() => changePage(id)}
            >
              <Icon size={19} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-status">
          <div className="live-indicator">
            <span />
            {/* Backend connected */}
          </div>
          <p>FastAPI · PostgreSQL · YouTube</p>
        </div>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <main className="main-content">
        <header className="topbar">
          <button
            type="button"
            className="mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMobileOpen(true)}
          >
            <Menu size={22} />
          </button>

          <div>
            <span className="eyebrow">{page.eyebrow}</span>
            <h1>{page.title}</h1>
            <p>{page.description}</p>
          </div>

          <div className="topbar-badge">
            <Radio size={16} />
            Kenya
          </div>
        </header>

        <section className="page-content">
          {activePage === "dashboard" && <DashboardPage />}
          {activePage === "rankings" && <RankingsPage />}
          {activePage === "assistant" && <AssistantPage />}
          {activePage === "knowledge" && <KnowledgePage />}
          {activePage === "ingestion" && <IngestionPage />}
        </section>
      </main>
    </div>
  );
}
