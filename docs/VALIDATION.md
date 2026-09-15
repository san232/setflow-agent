# 실행 검증 기록

검증일: **2026-09-15** · Windows · Python 3.12.14 프로젝트 가상환경

## 자동 테스트

실제 실행 명령:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q --junitxml=artifacts/submission/pytest-results.xml
```

실제 저장된 표준 출력의 마지막 줄:

```text
62 passed, 1 deselected, 1 warning in 23.83s
```

- [표준 출력](evidence/pytest-2026-09-15.txt)
- [JUnit XML](evidence/pytest-2026-09-15.xml)

공개 로그에서는 개인 PC 경로와 호스트 이름만 가렸다. 테스트 이름·결과·실행 시간은 그대로 유지했다.

기본 pytest 설정은 `live_openai` 표식의 테스트 1개를 선택에서 제외한다. 통과한 테스트는 정렬·곡선·입력 범위, 곡 CRUD, 저장된 결과 snapshot, JSON/M3U, 도구 등록·인자 검증·실행 로그, Demo 대화, 외부 응답을 대체한 Agent 루프, King Gnu 조사 데이터의 정합성을 검사한다. 경고 1개는 Starlette TestClient가 사용하는 anyio alias의 DeprecationWarning이다.

## 현재 카탈로그와 실제 브라우저 실행

`http://127.0.0.1:8765/`에서 서버 정상과 Demo Mode를 확인했다. 보관함에는 King Gnu **43곡**이 있으며, 곡별 다섯 수치와 조사 근거가 표시된다.

| 요청·동작 | 확인 결과 |
|---|---|
| 중반 절정형으로 플레이리스트를 만들어줘 | `generate_playlist`, `preset=mid_peak`, `song_ids=null` |
| 생성 결과 | Playlist #4, 43곡, 적합도 91.58, 표시 비용 361.99 |
| 플레이리스트 4를 보여줘 | `get_playlist`, `playlist_id=4`, 43곡 결과 조회 |
| 왜 이 순서로 배치했는지 설명해줘 | `explain_playlist`, `playlist_id=4`, 곡별 실제 전환 설명 |
| 플레이리스트 4를 JSON으로 내보내줘 | `export_playlist`, `format=json`, 다운로드 링크 반환 |
| Sorrows의 장르·악기·근거 펼치기 | 팝 록·펑크 태그, 와우 기타·슬랩 베이스, 공연 배치와 수치 표시 |

플레이리스트 ID는 이번 로컬 DB에서의 번호이며 새 설치에서는 달라질 수 있다. 같은 곡 ID·수치·Preset·가중치를 사용하면 순서와 점수를 재현할 수 있다. 캡처에서 보이는 일부 오래된 로그는 이전 개발 실행 기록이며, 보고서에는 현재 43곡 작업 부분을 사용했다.

## 실행 자료 위치

현재 캡처는 `docs/screenshots/submission/`에 있다. 전체 보관함의 총수와 정렬 곡선, 생성 결과, 자연어 요청·선택 인자, 실행 로그, 곡별 조사 근거를 담았다. 보고서는 글자 가독성을 위해 해당 부분을 잘라 배치하며 원본 PNG도 함께 제공한다.

테스트는 개인 PC 정보를 가린 실제 stdout과 JUnit XML을 제공하고 보고서에 결과 문자열을 그대로 인용했다. 앱의 실행 화면과 테스트 로그 문서를 구분했다. 상세 이미지별 설명은 [캡처 안내](SCREENSHOT_GUIDE.md)를 따른다.

## GitHub Actions 검증

공개 커밋 `576f86b`에서 Python 3.12와 잠금 의존성을 사용해 설치, `pip check`, `pytest -q`가 모두 성공했다. Ubuntu 실행 결과는 `62 passed, 1 deselected, 1 warning in 15.44s`다. [자동 테스트 실행 기록](https://github.com/san232/setflow-agent/actions/runs/34934928553)에서 확인할 수 있다.
