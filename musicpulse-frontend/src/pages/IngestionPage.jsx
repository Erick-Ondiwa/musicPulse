import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ChartNoAxesCombined,
  CheckCircle2,
  Clock,
  Database,
  Download,
  RefreshCw,
  Search,
  Server,
  Youtube,
} from "lucide-react";
import { musicApi } from "../api/client";

const jobs = [
  {
    id: "popular",
    title: "Popular music videos",
    description:
      "Fetch YouTube's most-popular music-category videos for the selected region.",
    icon: ChartNoAxesCombined,
    action: "Fetch popular",
  },
  {
    id: "recent",
    title: "Recent music discovery",
    description:
      "Search YouTube for music-category videos published inside the selected time window.",
    icon: Search,
    action: "Discover recent",
  },
  {
    id: "refresh",
    title: "Refresh stored statistics",
    description:
      "Retrieve current views, likes, and comments for all stored YouTube videos.",
    icon: RefreshCw,
    action: "Refresh metrics",
  },
];

export default function IngestionPage() {
  const queryClient = useQueryClient();
  const [regionCode, setRegionCode] = useState("KE");
  const [maxResults, setMaxResults] = useState(25);
  const [hours, setHours] = useState(24);
  const [activity, setActivity] = useState([]);

  const mutation = useMutation({
    mutationFn: async (jobId) => {
      if (jobId === "popular") {
        return {
          jobId,
          result: await musicApi.ingestPopular({ regionCode, maxResults }),
        };
      }
      if (jobId === "recent") {
        return {
          jobId,
          result: await musicApi.ingestRecent({
            regionCode,
            hours,
            maxResults,
          }),
        };
      }
      return {
        jobId,
        result: await musicApi.refreshStatistics(),
      };
    },
    onSuccess: ({ jobId, result }) => {
      const job = jobs.find((item) => item.id === jobId);
      setActivity((current) => [
        {
          id: crypto.randomUUID(),
          title: job.title,
          status: "success",
          timestamp: new Date(),
          result,
        },
        ...current,
      ]);
      queryClient.invalidateQueries();
    },
    onError: (error, jobId) => {
      const job = jobs.find((item) => item.id === jobId);
      setActivity((current) => [
        {
          id: crypto.randomUUID(),
          title: job.title,
          status: "error",
          timestamp: new Date(),
          error: error.message,
        },
        ...current,
      ]);
    },
  });

  return (
    <div className="content-stack">
      <article className="panel ingestion-config">
        <div className="config-heading">
          <div className="config-icon">
            <Youtube size={24} />
          </div>
          <div>
            <h2>YouTube collection settings</h2>
            <p>
              These values are applied to manually triggered ingestion jobs.
            </p>
          </div>
        </div>

        <div className="config-fields">
          <label>
            Region code
            <input
              value={regionCode}
              maxLength={2}
              onChange={(event) =>
                setRegionCode(event.target.value.toUpperCase())
              }
            />
          </label>

          <label>
            Maximum results
            <select
              value={maxResults}
              onChange={(event) => setMaxResults(Number(event.target.value))}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </label>

          <label>
            Recent window
            <select
              value={hours}
              onChange={(event) => setHours(Number(event.target.value))}
            >
              <option value={1}>1 hour</option>
              <option value={6}>6 hours</option>
              <option value={24}>24 hours</option>
              <option value={72}>3 days</option>
              <option value={168}>7 days</option>
            </select>
          </label>
        </div>
      </article>

      <div className="job-grid">
        {jobs.map(({ id, title, description, icon: Icon, action }) => {
          const running = mutation.isPending && mutation.variables === id;
          return (
            <article className="panel job-card" key={id}>
              <div className="job-icon">
                <Icon size={23} />
              </div>
              <h3>{title}</h3>
              <p>{description}</p>
              <button
                type="button"
                className="button primary"
                onClick={() => mutation.mutate(id)}
                disabled={mutation.isPending}
              >
                {running ? (
                  <RefreshCw size={17} className="spin" />
                ) : (
                  <Download size={17} />
                )}
                {running ? "Running..." : action}
              </button>
            </article>
          );
        })}
      </div>

      <article className="panel schedule-panel">
        <div className="schedule-row">
          <Clock size={20} />
          <div>
            <strong>Automatic collection schedule</strong>
            <p>Configured by Celery Beat in the backend.</p>
          </div>
        </div>
        <div className="schedule-tags">
          <span>Recent discovery · 15 min</span>
          <span>Statistics refresh · 10 min</span>
          <span>Popular collection · 30 min</span>
        </div>
      </article>

      <article className="panel">
        <div className="section-header">
          <div>
            <h2>Recent ingestion activity</h2>
            <p>Results from actions triggered in this browser session.</p>
          </div>
        </div>

        {activity.length === 0 ? (
          <div className="activity-empty">
            <Server size={28} />
            <div>
              <strong>No manual jobs run yet</strong>
              <p>Choose one of the ingestion actions above.</p>
            </div>
          </div>
        ) : (
          <div className="activity-list">
            {activity.map((item) => (
              <div className="activity-row" key={item.id}>
                <div
                  className={`activity-status ${
                    item.status === "success" ? "success" : "error"
                  }`}
                >
                  {item.status === "success" ? (
                    <CheckCircle2 size={18} />
                  ) : (
                    <Database size={18} />
                  )}
                </div>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.timestamp.toLocaleString()}</span>
                  {item.status === "success" ? (
                    <p>
                      Received {item.result.received ?? item.result.requested ?? 0},
                      inserted {item.result.inserted ?? 0}, updated{" "}
                      {item.result.updated ?? 0}, snapshots{" "}
                      {item.result.snapshots_created ?? 0}.
                    </p>
                  ) : (
                    <p>{item.error}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </article>
    </div>
  );
}
