# 제출 캡처 안내

2026-09-15 실행한 **King Gnu 43곡** 버전의 자료다. 원본은 아래 경로에 있다. 보고서에서는 필요한 화면 영역을 잘라 읽기 쉬운 크기로 배치했다.

| 파일 | 확인할 내용 |
|---|---|
| `screenshots/submission/01-library.png` | 보관함 총 43곡, 다섯 수치, mid_peak 목표·실제 곡선 |
| `screenshots/submission/02-flow.png` | 적합도 91.58, 비용 361.99, 43곡 결과와 시작 곡 |
| `screenshots/submission/03-tool-call.png` | 생성 요청, generate_playlist 성공, preset·song_ids·name |
| `screenshots/submission/04-logs.png` | 43곡 생성·조회·설명과 JSON 내보내기 성공 로그 |
| `screenshots/submission/05-research.png` | Sorrows의 장르·악기·공연 배치·주관적 초깃값 |

테스트 증거는 [실제 표준 출력](evidence/pytest-2026-09-15.txt)과 [JUnit XML](evidence/pytest-2026-09-15.xml)이다. 공개 파일은 개인 PC 경로와 호스트 이름만 가렸다. 결과는 `62 passed, 1 deselected, 1 warning in 23.83s`이며, 보고서에는 실제 저장된 로그를 인용했다.

새로 촬영할 때는 `README.md` 순서로 실행한 뒤 보관함 총수를 확인한다. 자연어 예시 버튼을 누른 후에는 **요청 보내기**까지 눌러야 도구가 실행된다. ‘Arguments와 요청 보기’를 펼쳐 사용자 문장과 실제 인자를 함께 기록한다. 현재 화면의 Mode와 사용한 곡 수가 보이거나 캡션에 명확히 적혀 있어야 한다.
