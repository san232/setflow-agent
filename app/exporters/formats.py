"""UTF-8 metadata exports; no audio files or fictional service URLs."""

import json
from urllib.parse import urlsplit

from app.application.ports import JsonObject
from app.exporters.base import ExportedFile


def one_line(value: object) -> str:
    """Prevent titles from injecting M3U directives or extra entries."""
    return " ".join(str(value).splitlines()).replace("\x00", "")


class JsonExporter:
    """Export the complete saved generation snapshot."""

    def export(self, playlist: JsonObject) -> ExportedFile:
        content = json.dumps(playlist, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
        return ExportedFile(content, "application/json", f"playlist-{playlist['id']}.json")


class M3UExporter:
    """Write playable entries only for explicit media references; preserve missing entries as comments."""

    def export(self, playlist: JsonObject) -> ExportedFile:
        lines = ["#EXTM3U", f"#PLAYLIST:{one_line(playlist['name'])}",
                 "# SetFlow: user-entered mood metadata; no audio is included."]
        missing = 0
        web_pages = 0
        items = playlist.get("items", [])
        if not isinstance(items, list):
            raise ValueError("Playlist items must be a list.")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("song"), dict):
                raise ValueError("Invalid playlist snapshot.")
            song = item["song"]
            title = one_line(f"{song['artist']} - {song['title']}")
            uri = song.get("media_uri")
            if uri:
                if urlsplit(str(uri)).hostname in ("youtube.com", "www.youtube.com", "music.youtube.com", "youtu.be"):
                    web_pages += 1
                lines.extend((f"#EXTINF:-1,{title}", one_line(uri)))
            else:
                missing += 1
                lines.append(f"#MISSING_MEDIA:{item['position']} | {title}")
        warnings = (f"{missing}곡의 재생 위치가 없어 M3U 주석으로만 기록했습니다. 재생하려면 곡의 media_uri를 입력하고 Playlist를 다시 생성하세요.",) if missing else ()
        if web_pages:
            warnings += (f"{web_pages}곡은 YouTube 웹페이지 링크입니다. 일반 M3U 플레이어에서 재생되지 않을 수 있으며, YouTube Music 계정 재생목록에는 자동 저장되지 않습니다.",)
        return ExportedFile(("\n".join(lines) + "\n").encode("utf-8"), "audio/x-mpegurl",
                            f"playlist-{playlist['id']}.m3u", warnings)
