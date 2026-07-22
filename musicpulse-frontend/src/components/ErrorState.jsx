import { AlertTriangle, RefreshCw } from "lucide-react";

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="state-card error-state">
      <AlertTriangle size={28} />
      <div>
        <strong>Unable to load data</strong>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button type="button" className="button secondary" onClick={onRetry}>
          <RefreshCw size={16} />
          Retry
        </button>
      )}
    </div>
  );
}
