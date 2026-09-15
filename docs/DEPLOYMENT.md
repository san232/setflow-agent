# SetFlow 웹 배포

**실행 사이트: [SetFlow](https://setflow-agent.onrender.com)** · Render Free · Singapore

GitHub 저장소는 소스 코드 주소이고, 실행 사이트는 Python 서버를 구동하는 호스팅에서 발급하는 HTTPS 주소다. 이 프로젝트는 FastAPI·SQLite·도구 실행을 포함하므로 정적 파일만 제공하는 GitHub Pages에서 그대로 실행되지 않는다. [GitHub Pages 안내](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)

## Render 무료 배포

1. [배포 시작](https://render.com/deploy?repo=https://github.com/san232/setflow-agent)을 열고 Render 계정으로 로그인한다.
2. 저장소 `san232/setflow-agent`와 `main` 브랜치의 Blueprint를 연다.
3. Web Service 1개, **Free**, Singapore, Python 설정을 확인하고 배포한다. 유료 DB·디스크는 설정하지 않는다.
4. 서비스가 **Live**가 되면 대시보드에 표시되는 실제 `https://…onrender.com` 주소를 연다. 이름 중복에 따라 주소가 달라질 수 있으므로 임의로 조합하지 않는다.
5. `/health`에서 정상 상태를 확인한 뒤 보관함 43곡, 플레이리스트 생성, 도구 로그, JSON 다운로드를 확인한다.

Blueprint 대신 **New → Web Service → Public Git Repository**를 사용해 공개 저장소 URL을 직접 넣어도 된다. 이 경우 아래 값을 입력한다.

| 설정 | 값 |
|---|---|
| Repository | `https://github.com/san232/setflow-agent` |
| Branch | `main` |
| Language | Python 3 |
| Region | Singapore |
| Instance Type | Free |
| Build Command | `python -m pip install -r requirements-lock.txt` |
| Start Command | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Auto Deploy | Off — 검증한 변경을 수동 배포 |

| 환경 변수 | 값 |
|---|---|
| `PYTHON_VERSION` | `3.12.14` |
| `PYTHONUTF8` | `1` |
| `SETFLOW_DEMO_MODE` | `true` |
| `SETFLOW_PUBLIC_DEMO` | `true` |
| `SETFLOW_AUTO_SEED` | `true` |
| `SETFLOW_DB_PATH` | `/tmp/setflow/setflow.db` |

OpenAI API 키는 입력하지 않는다. `SETFLOW_PUBLIC_DEMO=true`는 외부 모델 호출을 사용하지 않고 실제 서버의 Demo Router·정렬·도구를 실행한다. 공개 체험판 설정의 기본값은 `false`이며, 기본 곡 자동 등록(`SETFLOW_AUTO_SEED`)은 로컬과 배포 환경에서 모두 기본으로 켜져 있다.

## 접속과 데이터 저장

무료 서비스는 15분간 요청이 없으면 중지되며 다시 접속할 때 재시작 시간이 필요하다. 로컬 파일은 재배포·재시작·중지 시 유지되지 않는다. 배포 서버가 시작될 때 43곡을 불러오며, 파일이 유지된 상태에서는 기존 편집값을 덮어쓰지 않는다. 결과를 보관하려면 JSON/M3U를 다운로드한다. [Render 무료 서비스 안내](https://render.com/docs/free)

이 배포는 공유 체험판이다. 보관함·플레이리스트·요청 로그를 모든 방문자가 함께 사용한다는 안내를 화면 상단에 표시한다. 개인 자료를 계속 보관하려면 로컬 실행을 사용한다.

새 코드를 반영할 때는 GitHub의 **Python tests** 통과를 확인하고 Render의 **Manual Deploy → Deploy latest commit**을 실행한다. 배포 후 위 검증을 다시 확인한다.

## 설정 근거

- [FastAPI 배포와 포트 설정](https://render.com/docs/deploy-fastapi)
- [Blueprint 설정](https://render.com/docs/blueprint-spec)
- [Python 버전 지정](https://render.com/docs/python-version)
- [Deploy to Render 링크](https://render.com/docs/deploy-to-render)

## 배포 설정 검증

2026-09-15 로컬에서 전체 테스트 `65 passed, 1 deselected, 1 warning in 35.31s`를 확인했다. 추가 테스트는 시작 시 43곡 등록, 재시작 후 편집값 보존, 공개 체험판의 외부 API 호출 차단, 실제 도구를 통한 43곡 생성·JSON 다운로드와 배포 환경 변수 적용을 검사한다.

공개 코드 `15bec55`의 [GitHub 자동 테스트](https://github.com/san232/setflow-agent/actions/runs/34936993253)도 통과했다. [배포 설정 테스트 XML](evidence/pytest-deployment-2026-09-15.xml)은 PC 호스트 이름을 가린 실제 실행 기록이다.

2026-09-15 실제 HTTPS 사이트에서 기본 43곡, 자연어 요청의 `generate_playlist` 성공, 43곡 결과(적합도 91.58, 비용 361.9857), JSON·M3U 다운로드 HTTP 200을 확인했다. [공개 서버 검증 기록](evidence/hosted-2026-09-15.json)에 응답 요약을 남겼다.
