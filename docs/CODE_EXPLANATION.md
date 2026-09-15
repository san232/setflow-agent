# 주요 코드 설명

## 요청에서 실행까지

`POST /api/agent/chat` → `AgentService.chat()` → `DemoRouter.run()` → `ToolExecutor.execute()` → `ToolRegistry.invoke()` → Handler → Application 서비스 순서로 처리된다. Demo Mode의 문장 패턴으로 도구 이름과 인자를 정하고, 실제 정렬과 저장은 서버 코드가 수행한다.

## 도구 등록

`app/tools/registry.py`의 `ToolDefinition`은 다음 네 값을 연결한다.

```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: type[Command]
    handler: Handler
```

등록 목록의 `generate_playlist`는 `GeneratePlaylist` 인자 모델과 `handlers.generate_playlist`를 연결한다. 같은 방식으로 곡 등록·목록·수정·삭제, 플레이리스트 조회·설명·내보내기를 포함한 총 8개 도구를 등록한다.

`invoke()`는 이름이 Registry에 있는지 확인하고, `definition.parameters.model_validate(arguments)`를 통과한 인자만 Handler로 전달한다. 예를 들어 다섯 분위기 수치는 0~100의 정수로 검증한다.

## 요청에 따른 선택

`app/agent/demo.py`의 생성 분기는 ‘만들’, ‘생성’, ‘정렬’을 확인하고 목표 흐름 표현에서 Preset을 정한다. ‘중반’은 `mid_peak`로 연결된다. 곡 ID를 지정하지 않으면 `song_ids`는 `None`으로 전달되어 보관함 전체가 대상이 된다.

2026-09-15 실제 요청과 선택 결과:

```text
요청: 중반 절정형으로 플레이리스트를 만들어줘
도구: generate_playlist
인자: {"preset": "mid_peak", "song_ids": null,
       "name": "Demo Playlist"}
결과: 43곡, 적합도 91.58
```

최근 플레이리스트 ID는 대화 상태에 저장된다. 같은 대화의 ‘왜 이 순서로 배치했는지 설명해줘’는 `explain_playlist`로 연결되어 실제 생성 결과의 설명을 조회한다.

## 실행과 로그

`app/agent/executor.py`는 JSON 문자열 인자를 객체로 해석하고 Registry를 호출한다. JSON 형식 오류, Pydantic 검증 오류, 애플리케이션 오류를 구분해 결과를 만든다. `user_request`, `tool_name`, `arguments`, `success`, `result_summary`, `created_at`, `conversation_id`, `call_id`, `mode`를 모아 `self.logs.append(trace)`로 저장한다. 웹은 이 실제 기록을 표시한다.

## 순서를 계산하는 방법

`app/domain/curves.py`는 목표 곡선을, `scoring.py`는 위치별 비용을 계산한다. `optimizer.py`는 추가 비용이 작은 곡을 차례로 선택하고, 두 곡을 교환했을 때 전체 비용이 줄면 새 순서를 채택한다. 동점과 탐색 순서를 고정해 같은 입력의 결과를 재현한다.

```text
전체 비용 = 목표 에너지 차이 + 앞 곡과의 변화 비용
          + 마무리 적합도 부족 + 반복·큰 도약 비용
적합도 = max(0, 100 - 전체 비용 / 곡 수)
```

정확한 가중치는 `weights.py`에 있다. 이 적합도는 프로젝트의 주관적 수치와 비용 함수에 따른 값이다. `explanations.py`는 최종 순서의 앞 곡, 수치 변화, 주요 비용을 이용해 역할과 전환 이유를 만든다.

## 저장과 내보내기

`app/infrastructure/repositories.py`가 SQLite 저장을 담당한다. 생성 결과는 당시 곡 데이터의 snapshot을 포함한다. `app/exporters/`는 JSON과 M3U 파일 내용을 만든다. M3U는 `media_uri`가 있는 항목에 재생 위치를 기록하고, 나머지는 주석과 경고를 반환한다.

## 먼저 읽을 파일

| 순서 | 파일 | 확인할 부분 |
|---|---|---|
| 1 | `app/tools/registry.py` | 8개 도구 정의와 invoke |
| 2 | `app/agent/demo.py` | 문장별 선택과 인자 추출 |
| 3 | `app/agent/executor.py` | 실행, 오류 처리, 로그 저장 |
| 4 | `app/application/services.py` | 곡·플레이리스트 처리 |
| 5 | `app/domain/optimizer.py` | Greedy와 Swap |
| 6 | `app/static/app.js` | 요청, SVG 곡선, 결과·로그 표시 |

실행 증거는 [검증 기록](VALIDATION.md)과 [캡처 목록](SCREENSHOT_GUIDE.md)에 연결했다.
