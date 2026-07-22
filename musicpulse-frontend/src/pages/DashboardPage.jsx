import { useQueries } from "@tanstack/react-query";
import {
  Activity,
  Clock3,
  Eye,
  Music,
  UsersRound,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { musicApi } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import SectionHeader from "../components/SectionHeader";
import SongTable from "../components/SongTable";
import StatCard from "../components/StatCard";
import { formatNumber } from "../utils/formatters";

export default function DashboardPage() {
  const results = useQueries({
    queries: [
      {
        queryKey: ["trending", 8, 24],
        queryFn: () => musicApi.trendingSongs({ limit: 8, lookbackHours: 24 }),
      },
      {
        queryKey: ["latest", 8],
        queryFn: () => musicApi.latestSongs({ limit: 8 }),
      },
      {
        queryKey: ["artists", 8],
        queryFn: () => musicApi.topArtists({ limit: 8 }),
      },
      {
        queryKey: ["most-viewed", 8],
        queryFn: () => musicApi.mostViewedSongs({ limit: 8 }),
      },
    ],
  });

  const [trendingQuery, latestQuery, artistsQuery, viewedQuery] = results;
  const loading = results.some((query) => query.isLoading);
  const error = results.find((query) => query.error)?.error;

  if (loading) return <LoadingState />;
  if (error) {
    return (
      <ErrorState
        message={error.message}
        onRetry={() => results.forEach((query) => query.refetch())}
      />
    );
  }

  const trending = trendingQuery.data || [];
  const latest = latestQuery.data || [];
  const artists = artistsQuery.data || [];
  const mostViewed = viewedQuery.data || [];

  const totalViews = mostViewed.reduce((sum, song) => sum + Number(song.views || 0), 0);
  const totalGrowth = trending.reduce(
    (sum, song) => sum + Number(song.view_growth || 0),
    0,
  );

  const chartData = trending.slice(0, 6).map((song) => ({
    name: song.title.length > 16 ? `${song.title.slice(0, 16)}…` : song.title,
    growth: song.view_growth || 0,
  }));

  return (
    <div className="content-stack">
      <div className="stat-grid">
        <StatCard
          icon={Activity}
          label="Trending tracks"
          value={formatNumber(trending.length)}
          description="With sufficient metric snapshots"
          accent="purple"
        />
        <StatCard
          icon={Eye}
          label="Tracked views"
          value={formatNumber(totalViews)}
          description="Across the leading stored videos"
          accent="blue"
        />
        <StatCard
          icon={UsersRound}
          label="Artists monitored"
          value={formatNumber(artists.length)}
          description="Present in the current ranking set"
          accent="green"
        />
        <StatCard
          icon={Clock3}
          label="Recent growth"
          value={`+${formatNumber(totalGrowth)}`}
          description="Views gained in trend windows"
          accent="orange"
        />
      </div>

      <div className="dashboard-grid">
        <article className="panel chart-panel">
          <SectionHeader
            title="Fastest-growing songs"
            description="View growth measured from stored snapshots."
          />
          {chartData.length ? (
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={310}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 35 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="name"
                    angle={-24}
                    textAnchor="end"
                    height={65}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis tickFormatter={formatNumber} width={56} />
                  <Tooltip
                    formatter={(value) => [formatNumber(value), "View growth"]}
                    contentStyle={{
                      borderRadius: 12,
                      border: "1px solid rgba(148,163,184,.18)",
                    }}
                  />
                  <Bar dataKey="growth" radius={[8, 8, 0, 0]} fill="currentColor" className="chart-bar" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              title="No trend history yet"
              description="Refresh video statistics after enough time has passed to create a second snapshot."
            />
          )}
        </article>

        <article className="panel artist-panel">
          <SectionHeader
            title="Top artists"
            description="Ranked by aggregate stored YouTube views."
          />
          <div className="artist-list">
            {artists.map((artist, index) => (
              <div className="artist-row" key={artist.artist_id}>
                <span className="artist-rank">{index + 1}</span>
                <div className="artist-avatar">
                  {artist.artist?.charAt(0) || "A"}
                </div>
                <div className="artist-meta">
                  <strong>{artist.artist}</strong>
                  <span>{artist.video_count} stored video(s)</span>
                </div>
                <strong>{formatNumber(artist.total_views)}</strong>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="panel">
        <SectionHeader
          title="Trending now"
          description="Calculated from view velocity, engagement growth, and freshness."
        />
        {trending.length ? (
          <SongTable songs={trending} showTrend />
        ) : (
          <EmptyState
            title="Trending rankings are not available"
            description="The backend needs at least two snapshots for each video."
          />
        )}
      </article>

      <article className="panel">
        <SectionHeader
          title="Latest additions"
          description="The newest music videos stored in the database."
        />
        {latest.length ? <SongTable songs={latest} /> : <EmptyState />}
      </article>
    </div>
  );
}
