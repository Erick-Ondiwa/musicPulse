export default function StatCard({
  icon: Icon,
  label,
  value,
  description,
  accent = "purple",
}) {
  return (
    <article className={`stat-card accent-${accent}`}>
      <div className="stat-icon">
        <Icon size={21} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <p>{description}</p>
      </div>
    </article>
  );
}
