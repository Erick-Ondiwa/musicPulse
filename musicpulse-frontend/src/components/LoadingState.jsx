import { LoaderCircle } from "lucide-react";

export default function LoadingState({ label = "Loading music intelligence..." }) {
  return (
    <div className="state-card">
      <LoaderCircle className="spin" size={28} />
      <p>{label}</p>
    </div>
  );
}
