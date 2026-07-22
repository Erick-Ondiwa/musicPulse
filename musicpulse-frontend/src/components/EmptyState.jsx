import { Music2 } from "lucide-react";

export default function EmptyState({
  title = "No music data yet",
  description = "Run an ingestion job or load the included demo data.",
}) {
  return (
    <div className="state-card">
      <Music2 size={28} />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}
