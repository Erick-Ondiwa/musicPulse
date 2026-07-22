from datetime import datetime, timedelta, timezone
import re
import httpx

from app.core.config import get_settings


class YouTubeAPIError(RuntimeError):
    pass


class YouTubeClient:
    base_url = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str | None = None, transport: httpx.BaseTransport | None = None):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.youtube_api_key
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0, transport=transport)

    def _get(self, path: str, params: dict) -> dict:
        if not self.api_key:
            raise YouTubeAPIError("YOUTUBE_API_KEY is missing.")
        params = {**params, "key": self.api_key}
        response = self.client.get(path, params=params)
        if response.is_error:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise YouTubeAPIError(f"YouTube API error {response.status_code}: {detail}")
        return response.json()

    def most_popular_music(self, region_code: str, max_results: int = 25) -> list[dict]:
        data = self._get(
            "/videos",
            {
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": region_code,
                "videoCategoryId": "10",
                "maxResults": min(max_results, 50),
            },
        )
        return [self._normalize_video(item, region_code) for item in data.get("items", [])]

    def recent_music(self, region_code: str, hours: int = 24, max_results: int = 25) -> list[dict]:
        published_after = datetime.now(timezone.utc) - timedelta(hours=hours)
        search_data = self._get(
            "/search",
            {
                "part": "snippet",
                "type": "video",
                "videoCategoryId": "10",
                "regionCode": region_code,
                "order": "date",
                "publishedAfter": published_after.isoformat().replace("+00:00", "Z"),
                "maxResults": min(max_results, 50),
            },
        )
        ids = [
            item.get("id", {}).get("videoId")
            for item in search_data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]
        return self.video_details(ids, region_code)

    def video_details(self, video_ids: list[str], region_code: str | None = None) -> list[dict]:
        if not video_ids:
            return []
        output: list[dict] = []
        for start in range(0, len(video_ids), 50):
            batch = video_ids[start:start + 50]
            data = self._get(
                "/videos",
                {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(batch),
                    "maxResults": 50,
                },
            )
            output.extend(self._normalize_video(item, region_code) for item in data.get("items", []))
        return output

    @staticmethod
    def _parse_duration_seconds(value: str | None) -> int | None:
        if not value:
            return None
        pattern = re.compile(
            r"P(?:(?P<days>\d+)D)?T"
            r"(?:(?P<hours>\d+)H)?"
            r"(?:(?P<minutes>\d+)M)?"
            r"(?:(?P<seconds>\d+)S)?"
        )
        match = pattern.fullmatch(value)
        if not match:
            return None
        parts = {key: int(number or 0) for key, number in match.groupdict().items()}
        return (
            parts["days"] * 86400
            + parts["hours"] * 3600
            + parts["minutes"] * 60
            + parts["seconds"]
        )

    @classmethod
    def _normalize_video(cls, item: dict, region_code: str | None) -> dict:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("maxres")
            or thumbnails.get("standard")
            or thumbnails.get("high")
            or thumbnails.get("medium")
            or thumbnails.get("default")
            or {}
        )
        published = snippet.get("publishedAt")
        if not published:
            raise YouTubeAPIError(f"Video {item.get('id')} is missing publishedAt")
        return {
            "external_id": item["id"],
            "title": snippet.get("title", "Untitled"),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle", "Unknown artist"),
            "published_at": datetime.fromisoformat(published.replace("Z", "+00:00")),
            "thumbnail_url": thumbnail.get("url"),
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "duration_seconds": cls._parse_duration_seconds(item.get("contentDetails", {}).get("duration")),
            "region_code": region_code,
            "category_id": snippet.get("categoryId"),
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "comment_count": int(statistics.get("commentCount", 0)),
        }
