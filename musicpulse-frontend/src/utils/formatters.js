export function formatNumber(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat("en", {
    notation: number >= 1_000_000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(number);
}

export function formatFullNumber(value) {
  return new Intl.NumberFormat("en-KE").format(Number(value || 0));
}

export function formatDate(value) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat("en-KE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatRelativeTime(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  const intervals = [
    { unit: "day", seconds: 86_400 },
    { unit: "hour", seconds: 3_600 },
    { unit: "minute", seconds: 60 },
  ];

  for (const interval of intervals) {
    if (Math.abs(seconds) >= interval.seconds) {
      return formatter.format(
        Math.round(seconds / interval.seconds),
        interval.unit,
      );
    }
  }

  return "just now";
}
