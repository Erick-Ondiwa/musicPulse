import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Clock, Eye, Flame, RefreshCw } from "lucide-react";
import { musicApi } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import SectionHeader from "../components/SectionHeader";
import SongTable from "../components/SongTable";

const tabs = [
  { id: "trending", label: "Trending", icon: Flame },
  { id: "latest", label: "Latest", icon: Clock },
  { id: "viewed", label: "Most viewed", icon: Eye },
];

export default function RankingsPage() {
  const [activeTab, setActiveTab] = useState("trending");
  const [limit, setLimit] = useState(10);
  const [lookback, setLookback] = useState(24);

  const query = useQuery({
    queryKey: ["ranking-page", activeTab, limit, lookback],
    queryFn: () => {
      if (activeTab === "trending") {
        return musicApi.trendingSongs({
          limit,
          lookbackHours: lookback,
        });
      }
      if (activeTab === "latest") {
        return musicApi.latestSongs({ limit });
      }
      return musicApi.mostViewedSongs({ limit });
    },
  });

  return (
    <div className="content-stack">
      <div className="ranking-toolbar panel">
        <div className="tab-list">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`tab-button ${activeTab === id ? "active" : ""}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </div>

        <div className="filter-row">
          {activeTab === "trending" && (
            <label>
              Lookback
              <select
                value={lookback}
                onChange={(event) => setLookback(Number(event.target.value))}
              >
                <option value={1}>1 hour</option>
                <option value={6}>6 hours</option>
                <option value={24}>24 hours</option>
                <option value={72}>3 days</option>
                <option value={168}>7 days</option>
              </select>
            </label>
          )}

          <label>
            Results
            <select
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            >
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
              <option value={50}>Top 50</option>
            </select>
          </label>

          <button
            type="button"
            className="button secondary"
            onClick={() => query.refetch()}
            disabled={query.isFetching}
          >
            <RefreshCw size={16} className={query.isFetching ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      <article className="panel">
        <SectionHeader
          title={tabs.find((tab) => tab.id === activeTab)?.label}
          description={
            activeTab === "trending"
              ? "Application-defined ranking using stored metric growth."
              : activeTab === "latest"
                ? "Ordered by YouTube publication timestamp."
                : "Ordered by the latest stored YouTube view count."
          }
        />

        {query.isLoading && <LoadingState label="Loading rankings..." />}
        {query.error && (
          <ErrorState
            message={query.error.message}
            onRetry={() => query.refetch()}
          />
        )}
        {!query.isLoading && !query.error && query.data?.length > 0 && (
          <SongTable songs={query.data} showTrend={activeTab === "trending"} />
        )}
        {!query.isLoading && !query.error && !query.data?.length && (
          <EmptyState
            title="No ranking results"
            description={
              activeTab === "trending"
                ? "Create more metric snapshots, then refresh this ranking."
                : "Run a YouTube ingestion job to populate the database."
            }
          />
        )}
      </article>
    </div>
  );
}
