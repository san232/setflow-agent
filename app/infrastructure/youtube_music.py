"""Unauthenticated ytmusicapi adapter with bounded requests and a small TTL cache."""

from collections import OrderedDict
from copy import deepcopy
import re
from threading import Lock
from time import monotonic

import requests
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL

from app.application.errors import AppError
from app.application.ports import JsonObject

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class SearchSession(requests.Session):
    """Bound visitor-data/search/continuation requests without retaining credentials."""

    def __init__(self) -> None:
        super().__init__()
        self.deadline = monotonic() + 20
        self.remaining = 3

    def request(self, method: str, url: str, **kwargs: object) -> requests.Response:
        remaining_time = self.deadline - monotonic()
        if self.remaining <= 0 or remaining_time <= 0:
            raise requests.Timeout("Search request budget exhausted")
        self.remaining -= 1
        kwargs["timeout"] = min(8, remaining_time)
        return super().request(method, url, **kwargs)


def clean_text(value: object, maximum: int = 200) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", value).split())[:maximum]


def normalize_results(raw: object, limit: int) -> list[JsonObject]:
    """Allow only usable metadata and construct URLs from validated video IDs."""
    if not isinstance(raw, list):
        raise ValueError("Invalid search response")
    results: list[JsonObject] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        video_id = item.get("videoId")
        title = clean_text(item.get("title"))
        artists = item.get("artists")
        names = [clean_text(a.get("name")) for a in artists if isinstance(a, dict)] if isinstance(artists, list) else []
        artist = ", ".join(dict.fromkeys(n for n in names if n))[:200]
        if not isinstance(video_id, str) or not VIDEO_ID.fullmatch(video_id) or video_id in seen or not title or not artist:
            continue
        seen.add(video_id)
        album = item.get("album")
        results.append({"video_id": video_id, "title": title, "artist": artist,
                        "source": "YouTube Music", "channel": "",
                        "album": clean_text(album.get("name")) if isinstance(album, dict) else "",
                        "duration": clean_text(item.get("duration"), 20),
                        "kind": "videos" if item.get("resultType") == "video" else "songs",
                        "media_uri": f"https://music.youtube.com/watch?v={video_id}",
                        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/default.jpg"})
        if len(results) >= limit:
            break
    return results


class QuietSearchLogger:
    def debug(self, message: str) -> None: pass
    def warning(self, message: str) -> None: pass
    def error(self, message: str) -> None: pass


class MetadataYoutubeDL(YoutubeDL):
    """Limit network work even if the upstream search extractor changes."""

    def __init__(self, options: dict) -> None:
        self.deadline = monotonic() + 20
        self.remaining = 3
        super().__init__(options)

    def urlopen(self, request):
        if self.remaining <= 0 or monotonic() >= self.deadline:
            raise requests.Timeout("Video search request budget exhausted")
        self.remaining -= 1
        return super().urlopen(request)


def search_youtube(query: str, limit: int) -> list[JsonObject]:
    """Read flat search metadata only; never open a stream or download media."""
    options = {"extract_flat": True, "skip_download": True, "quiet": True,
               "no_warnings": True, "logger": QuietSearchLogger(), "socket_timeout": 8,
               "retries": 0, "extractor_retries": 0, "cachedir": False, "playlistend": limit}
    with MetadataYoutubeDL(options) as client:
        raw = client.extract_info(f"ytsearch{limit}:{query}", download=False)
    entries = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise ValueError("Invalid video search response")
    results: list[JsonObject] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        video_id, title = entry.get("id"), clean_text(entry.get("title"))
        if not isinstance(video_id, str) or not VIDEO_ID.fullmatch(video_id) or video_id in seen or not title:
            continue
        seen.add(video_id)
        duration = entry.get("duration")
        seconds = int(duration) if isinstance(duration, (float, int)) and 0 <= duration <= 604800 else None
        results.append({"video_id": video_id, "title": title, "artist": "", "album": "",
                        "channel": clean_text(entry.get("channel") or entry.get("uploader")),
                        "duration": f"{seconds // 60}:{seconds % 60:02}" if seconds is not None else "",
                        "kind": "videos", "source": "YouTube",
                        "media_uri": f"https://www.youtube.com/watch?v={video_id}",
                        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/default.jpg"})
        if len(results) >= limit:
            break
    return results


class YouTubeMusicSearch:
    """No API key, browser cookies, user login, or network access at startup."""

    def __init__(self) -> None:
        self.cache: OrderedDict[tuple[str, str, int], tuple[float, list[JsonObject]]] = OrderedDict()
        self.lock = Lock()

    def search(self, query: str, kind: str, limit: int) -> list[JsonObject]:
        if not self.lock.acquire(blocking=False):
            raise AppError("다른 음악 검색을 처리 중입니다. 잠시 후 다시 검색하세요.", 503)
        try:
            key = (query.casefold(), kind, limit)
            cached = self.cache.get(key)
            if cached and monotonic() - cached[0] < 300:
                self.cache.move_to_end(key)
                return deepcopy(cached[1])
            try:
                results = []
                if kind == "songs":
                    try:
                        with SearchSession() as session:
                            client = YTMusic(requests_session=session, language="en", location="KR")
                            results = normalize_results(client.search(query, filter="songs", limit=limit), limit)
                    except Exception:
                        # Some regions/accounts receive no catalog songs while public videos work.
                        pass
                if not results:
                    results = search_youtube(query, limit)
            except Exception as error:
                # The third-party parser can also raise KeyError/TypeError on upstream changes.
                # Never expose upstream response bodies, headers, or internal exceptions.
                raise AppError("YouTube 검색에 연결하지 못했습니다. 잠시 후 다시 시도하거나 아래에서 YouTube 검색을 여세요.", 502) from error
            self.cache[key] = (monotonic(), results)
            self.cache.move_to_end(key)
            while len(self.cache) > 64:
                self.cache.popitem(last=False)
            return deepcopy(results)
        finally:
            self.lock.release()
