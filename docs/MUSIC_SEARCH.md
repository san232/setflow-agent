# YouTube 곡 검색

검색 결과를 선택해 제목·아티스트와 재생 링크를 등록 폼으로 가져온다. 저장 버튼을 누르기 전에는 보관함을 수정하지 않는다. 기존 곡은 분위기 수치를 유지하며, 보관함의 ‘링크 찾기’로 연결 대상을 명시할 수 있다. 새 곡의 수치는 사용자가 입력하고, 정확히 일치하는 King Gnu 조사 곡에만 기존 조사 초깃값을 사용한다.

## 요청과 실행

`GET /api/music/search?query=King%20Gnu&kind=songs&limit=8`에서 `kind`는 `songs` 또는 `videos`, `limit`은 1~10, 검색어는 공백 제거 후 1~200자다. `search_music` 도구도 같은 사용 사례를 실행한다. Demo Mode 예시는 ‘유튜브에서 King Gnu 白日 검색해줘’다. 결과 선택·저장은 화면에서 별도로 한다.

`app/application/music_search.py`는 요청 모델과 검색 계약을, `app/infrastructure/youtube_music.py`는 외부 검색을 담당한다. `app/static/music-search.js`에서 결과를 표시하고 등록 폼으로 옮긴다. 기존 곡의 값을 바꾸거나 새 수치를 추측하는 처리는 검색 서비스에 없다.

## 검색 공급자

- 곡 우선: `ytmusicapi`로 인증 없는 공개 곡 메타데이터를 요청한다.
- 곡 검색이 비거나 실패한 경우 및 영상 검색: `yt-dlp`의 flat 검색으로 일반 YouTube 영상 제목·채널·길이·영상 ID를 가져온다. `download=False`, `extract_flat=True`, `skip_download=True`이며 음원/영상 스트림을 내려받지 않는다.
- 일반 영상 검색의 채널은 아티스트로 간주하지 않는다. 새 곡 등록 때 아티스트를 직접 확인한다.
- 인증 파일, 브라우저 쿠키, 다른 프로젝트 로그인 정보를 사용하지 않는다. 시작 시 외부 요청도 하지 않는다.
- 외부 요청 수와 시간, 반환 결과 수를 제한한다. 검색 결과 캐시는 최대 64개, 5분이며 동시에 한 검색을 처리한다. 실패는 502/503 안내로 보여 주고 외부 응답 본문은 노출하지 않는다.
- 영상 ID를 검증해 링크를 직접 구성하고, 제목은 화면에서 `textContent`로 표시한다. 외부 문자열을 HTML이나 실행 명령으로 사용하지 않는다.

검색은 외부 서비스의 공개 응답에 의존한다. YouTube Music이 곡 결과를 반환하지 않는 경우가 실제로 확인되어 일반 YouTube 검색을 연결했다. 둘 다 연결되지 않으면 화면의 외부 검색 링크로 이어갈 수 있다.

## 링크와 내보내기

선택한 링크는 기존 `media_uri`에 저장한다. 보관함과 새로 생성한 플레이리스트에 ‘YouTube 열기’ 또는 ‘YouTube Music 열기’가 표시된다. 기존 플레이리스트는 생성 당시 스냅샷이므로 링크 연결 후 다시 생성해야 반영된다.

JSON/M3U에 링크를 포함할 수 있지만 YouTube 웹페이지는 음원 파일 URL이 아니다. 일반 M3U 플레이어에서 재생되지 않을 수 있고 YouTube Music 계정의 재생목록에 자동 저장되지 않는다. M3U 출력과 에이전트 답변에 이 안내를 포함한다. 계정 재생목록 생성은 별도 사용자 인증이 필요한 후속 기능이다.

## 검증

기본 Python 테스트는 외부 검색 응답을 대체해 입력 검증, 검색의 읽기 전용 동작, 선택 링크 저장, 기존 수치 유지, M3U 안내, 도구 선택·성공·실패 로그, 캐시와 공급자 전환을 확인한다. 실제 공개 검색 확인은 자동 테스트와 별도로 실행한다.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q
node tests/frontend/music-search.test.cjs
```

Frontend 검증은 Node.js 기본 모듈만 사용하며 개발 검증용이다. 서버 실행에 Node.js는 필요하지 않다.

참고: [ytmusicapi 사용법](https://ytmusicapi.readthedocs.io/en/stable/usage.html), [yt-dlp Python 사용법](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp), [YouTube 재생목록 생성과 OAuth 권한](https://developers.google.com/youtube/v3/docs/playlists/insert).
