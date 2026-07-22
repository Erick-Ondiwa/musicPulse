from datetime import datetime, timezone
import re
from sqlalchemy.orm import Session

from app.services.analytics import AnalyticsService


def _extract_limit(question: str, default: int = 10) -> int:
    match = re.search(r"\btop\s+(\d{1,2})\b", question.lower())
    if match:
        return min(max(int(match.group(1)), 1), 50)
    return default


def _format_number(value: int | float) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


class DeterministicAssistantService:
    def __init__(self, db: Session):
        self.analytics = AnalyticsService(db)

    def ask(self, question: str) -> dict:
        q = question.lower().strip()
        limit = _extract_limit(q)

        if any(term in q for term in ("trending", "growing fastest", "most momentum")):
            hours = 1 if "hour" in q else 24
            data = self.analytics.trending(limit=limit, lookback_hours=hours)
            return self._response(
                question,
                "trending_songs",
                self._song_list_answer(data, "trending songs", trend=True),
                data,
                (
                    f"Trending is an application-defined score based on YouTube view and "
                    f"engagement growth over the last {hours} hour(s), plus freshness."
                ),
            )

        if any(term in q for term in ("artists", "artist")) and any(
            term in q for term in ("most listened", "top", "most viewed", "listened to the most")
        ):
            data = self.analytics.top_artists(limit)
            lines = [
                f"{index}. {row['artist']} — {_format_number(row['total_views'])} total current views "
                f"across {row['video_count']} stored video(s)"
                for index, row in enumerate(data, 1)
            ]
            answer = "Top artists by aggregate YouTube views:\n" + ("\n".join(lines) if lines else "No data available.")
            return self._response(
                question,
                "top_artists",
                answer,
                data,
                "For this YouTube MVP, 'listened to' is approximated using current YouTube video views.",
            )

        if any(term in q for term in ("last hour", "past hour", "an hour ago", "one hour")):
            data = self.analytics.latest(limit=limit, hours=1)
            return self._response(
                question,
                "released_last_hour",
                self._song_list_answer(data, "videos published in the last hour"),
                data,
                "Release time means the YouTube video's publishedAt timestamp, not a verified commercial release time.",
            )

        if any(term in q for term in ("latest", "newest", "recently released", "new releases")):
            data = self.analytics.latest(limit=limit)
            return self._response(
                question,
                "latest_releases",
                self._song_list_answer(data, "latest stored music videos"),
                data,
                "Latest is ordered by the YouTube publishedAt timestamp.",
            )

        if any(term in q for term in ("most viewed", "top songs", "popular songs", "highest views")):
            hours = 24 if any(term in q for term in ("today", "24 hours", "past day")) else None
            data = self.analytics.most_viewed(limit=limit, published_within_hours=hours)
            label = "most-viewed songs published in the last 24 hours" if hours else "most-viewed stored songs"
            return self._response(
                question,
                "most_viewed_songs",
                self._song_list_answer(data, label),
                data,
                "Ranking uses the latest YouTube viewCount stored by the system.",
            )

        quoted = re.search(r'["“](.+?)["”]', question)
        if quoted or any(term in q for term in ("how is", "performance of", "statistics for")):
            phrase = quoted.group(1) if quoted else self._extract_search_phrase(question)
            data = self.analytics.search_song(phrase)
            return self._response(
                question,
                "song_search",
                self._song_list_answer(data, f'matches for "{phrase}"'),
                data,
                "Results are title matches from the local database and show the latest stored YouTube metrics.",
            )

        return self._response(
            question,
            "unsupported",
            (
                "I could not map that question to an approved MVP analytics function. "
                "Try asking for trending songs, latest releases, uploads from the last hour, "
                "most-viewed songs, top artists, or the performance of a named song."
            ),
            [],
            "No database metric was selected.",
        )

    @staticmethod
    def _extract_search_phrase(question: str) -> str:
        lowered = question.lower()
        for prefix in ("how is", "performance of", "statistics for"):
            index = lowered.find(prefix)
            if index >= 0:
                return question[index + len(prefix):].strip(" ?.")
        return question.strip(" ?.")

    @staticmethod
    def _song_list_answer(data: list[dict], label: str, trend: bool = False) -> str:
        if not data:
            return f"No {label} are available in the database yet."
        lines = []
        for index, row in enumerate(data, 1):
            suffix = (
                f" — +{_format_number(row.get('view_growth', 0))} views, "
                f"{_format_number(row.get('view_velocity_per_hour', 0))}/hour"
                if trend
                else f" — {_format_number(row['views'])} views"
            )
            lines.append(f"{index}. {row['title']} — {row['artist']}{suffix}")
        return f"Here are the {label}:\n" + "\n".join(lines)

    @staticmethod
    def _response(question: str, intent: str, answer: str, data: list[dict], metric: str) -> dict:
        return {
            "question": question,
            "intent": intent,
            "answer": answer,
            "data": data,
            "metric_definition": metric,
            "generated_at": datetime.now(timezone.utc),
        }
