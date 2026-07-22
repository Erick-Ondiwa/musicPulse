import { ExternalLink, Eye, TrendingUp } from "lucide-react";
import {
  formatFullNumber,
  formatRelativeTime,
} from "../utils/formatters";

export default function SongTable({ songs, showTrend = false }) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Song</th>
            <th>Published</th>
            <th>Views</th>
            {showTrend && <th>Growth</th>}
            {showTrend && <th>Velocity</th>}
            <th />
          </tr>
        </thead>
        <tbody>
          {songs.map((song, index) => (
            <tr key={song.video_id || song.youtube_id}>
              <td>
                <span className={`rank-badge rank-${index + 1}`}>
                  {index + 1}
                </span>
              </td>
              <td>
                <div className="song-cell">
                  <div className="song-thumbnail">
                    {song.thumbnail_url ? (
                      <img src={song.thumbnail_url} alt="" />
                    ) : (
                      <span>{song.title?.charAt(0) || "M"}</span>
                    )}
                  </div>
                  <div>
                    <strong>{song.title}</strong>
                    <span>{song.artist}</span>
                  </div>
                </div>
              </td>
              <td>{formatRelativeTime(song.published_at)}</td>
              <td>
                <span className="metric-inline">
                  <Eye size={14} />
                  {formatFullNumber(song.views)}
                </span>
              </td>
              {showTrend && (
                <td className="positive">
                  +{formatFullNumber(song.view_growth)}
                </td>
              )}
              {showTrend && (
                <td>
                  <span className="metric-inline">
                    <TrendingUp size={14} />
                    {formatFullNumber(song.view_velocity_per_hour)}/h
                  </span>
                </td>
              )}
              <td>
                <a
                  className="icon-link"
                  href={song.url}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Open ${song.title} on YouTube`}
                >
                  <ExternalLink size={17} />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
