# King Gnu 초깃값과 조사 근거

King Gnu 대표 공연 7개(2019~2025)와 곡·장르·악기 자료를 참고한 주관적 초깃값입니다. 실측 음원 분석·공식 점수·역대 전수조사가 아닙니다. 공연 편곡은 원곡과 다를 수 있으며 직접 수정할 수 있습니다.

자료 확인일: 2026-09-15. 이 문서는 `python -m scripts.build_king_gnu`로 재생성합니다.

## 수집 범위

연도와 투어가 다른 대표 공연 7개를 수작업으로 대조했습니다. 역대 모든 공연, 전곡 목록, 2026년 최신 투어를 포괄하지 않습니다. 같은 투어의 여러 날짜를 많이 넣어 특정 편곡이 과대표집되는 것을 피했습니다. 이 표본은 임의로 고른 것으로 통계적 대표성을 보장하지 않습니다.

| 날짜 | 공연 | 장소 | 세트리스트 출처 |
|---|---|---|---|
| 2019-11-26 | Live Tour 2019 AW FINAL | Zepp Tokyo | [AWA 공식 발표](https://prtimes.jp/main/html/rd/p/000000733.000022425.html) |
| 2020-12-06 | Live Tour 2020 AW CEREMONY | Makuhari Messe | [음악 나탈리 공연 보도](https://natalie.mu/music/news/407728) |
| 2021-12-15 | Live Tour 2021 AW | Yoyogi National Gymnasium | [음악 나탈리 공연 보도](https://natalie.mu/music/news/457875) |
| 2022-11-20 | Live at TOKYO DOME | Tokyo Dome | [음악 나탈리 공연 보도](https://natalie.mu/music/news/502139) · [Fender 현장 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/) |
| 2023-06-04 | Stadium Live Tour 2023 CLOSING CEREMONY | Nissan Stadium | [음악 나탈리 공연 보도](https://natalie.mu/music/news/527459) |
| 2024-01-28 | Dome Tour THE GREATEST UNKNOWN | Tokyo Dome | [음악 나탈리 공연 보도](https://natalie.mu/music/news/566755) · [Sony Music 공식 영상 수록 순서](https://www.sonymusic.co.jp/artist/kinggnu/info/567342) |
| 2025-04-09 | LIVEHOUSE TOUR 2025 CLUB GNU EDITION | Tokyo Garden Theater | [음악 나탈리 공연 보도](https://natalie.mu/music/news/619979) |

원자료에는 연결 트랙과 게스트 곡도 원래 순서로 남겼습니다. 아래 항목을 정렬 대상과 통계에서 제외한 뒤 43곡을 선정했습니다. `NIGHT POOL`은 공연의 확장 편곡을 다룬 악기 자료가 있어 포함했고, `MASCARA`는 Sony가 발매를 확인한 King Gnu 셀프 커버 버전으로 포함했습니다.

- 開会式: SE/연결 트랙
- 閉会式: SE/연결 트랙
- 幕間: 연결 트랙
- MIRROR: 초기 후보에서는 TGU 연결 소곡 제외
- DARE??: 초기 후보에서는 TGU 연결 소곡 제외
- W●RKAHOLIC: 초기 후보에서는 TGU 연결 소곡 제외
- δ: 초기 후보에서는 TGU 연결 소곡 제외
- SUNNY SIDE UP: 초기 후보에서는 TGU 연결 소곡 제외
- 仝: 초기 후보에서는 TGU 연결 소곡 제외
- ЯOЯЯIM: 초기 후보에서는 TGU 연결 소곡 제외
- W●RK: millennium parade × 椎名林檎 게스트 곡; King Gnu 후보에서 제외

`ロウラブ → ロウラヴ`, `Stardom → STARDOM`, `CHAMELEON → カメレオン`으로 묶었습니다. 원문 제목은 각 출현 기록의 `source_title`에 보존합니다. 카멜레온의 버전별 편곡 차이는 이 초기 모델에서 별도 곡으로 나누지 않습니다.

## 사실과 주관적 수치의 구분

공연 날짜·순서와 출처가 서술한 악기·음색은 자료에 근거합니다. 장르 태그는 리뷰의 설명을 정리한 편집 태그이며 공식 장르 분류가 아닙니다. `instruments`는 언급된 일부 악기·보컬·처리 음색만 기록합니다. 현악 음색이나 목금 음색의 언급을 실제 연주자의 악기 크레딧으로 바꾸지 않았습니다. 공연용 어쿠스틱 편곡은 해당 공연의 특징입니다.

다섯 기본값은 조사 내용을 읽고 수작업으로 정한 가설입니다. 악기가 몇 개라는 이유만으로 밀도를 계산하지 않으며, 음원 분석·BPM 측정·감정 인식 모델·공식 수치·객관적 정답은 사용하지 않았습니다. 직접 들어본 본인의 판단으로 수정하는 용도입니다.

| 필드 | 낮은 값 → 높은 값 |
|---|---|
| energy | 억제된 추진력 → 강한 추진력·공격성 |
| valence | 어둡거나 우울한 인상 → 밝거나 낙관적인 인상 |
| tension | 안정·완화 → 불안·긴장·급격한 전개 |
| density | 여백이 많은 편성 → 겹치는 음색·리듬이 많은 편성 |
| closure | 연결 구간에 어울림 → 종결·합창·여운에 어울림 |

## 공연 배치 반영식

본편과 앙코르를 각각 분리하고, 선정 곡의 구간 내 순서를 0~1로 정규화합니다. 시작부터 끝까지 에너지가 단조 증가한다고 가정하지 않습니다. 아래 곡선은 실제 콘서트의 측정치가 아니라 이 프로젝트가 정한 임의의 보조 템플릿입니다.

- 본편: `(0,88), (0.18,78), (0.45,32), (0.62,52), (0.85,90), (1,82)` 사이를 선형 보간.
- 앙코르·더블 앙코르 각각: `(0,60), (0.5,88), (1,55)` 사이를 선형 보간. 1곡 구간은 위치 0으로 취급.
- 종료 근거 점수: 공연 전체 마지막 100, 그 외 본편 마지막 80, 그 외 앙코르 60, 나머지 본편 20. 제외 트랙을 제거한 뒤 판단.
- 해당 곡 출현 횟수가 n일 때, 배치 점수 = `(50×2 + 각 출현의 템플릿 에너지 합) / (n+2)`.
- 종료 점수 = `(50×2 + 각 출현의 종료 근거 점수 합) / (n+2)`.
- 최종 energy = `round(0.85×음악 기본값 + 0.15×배치 점수)`.
- 최종 closure = `round(0.55×음악 기본값 + 0.45×종료 점수)`.
- valence / tension / density는 음악 자료에 따른 기본값 그대로 사용.

두 번의 중립 관측(50)을 추가해 한 공연의 배치만으로 값을 과도하게 바꾸지 않게 했습니다. 가중치와 곡선은 학습한 결과가 아닌 편집 규칙이며 모든 곡에 동일하게 적용합니다. 반올림은 Python round의 ties-to-even입니다. 음악 기본값과 최종값은 0~100 정수입니다.

`source_position`은 저장한 원자료에서 연결 트랙을 포함한 연속 순번입니다. 기사에 인쇄된 곡 번호와 다를 수 있습니다. `position`, `section_position`은 제외 트랙을 제거한 전체·구간 내 순번입니다. `mean_position`은 선정 곡 기준 전체 상대 위치의 평균(0~1)입니다. 공연 출현 횟수는 이 표본 7개 안에서의 횟수이며 역대 연주 횟수가 아닙니다.

## 43곡 최종 초깃값

장르·악기를 참고한 음악 기본값에 위 배치 보정을 반영한 값입니다. 이 값이 보관함에 들어갑니다.

| 곡 | 에너지 | 밝기 | 긴장 | 밀도 | 마무리 | 표본 출현 |
|---|---:|---:|---:|---:|---:|---:|
| 飛行艇 | 91 | 72 | 80 | 90 | 58 | 7 |
| Sorrows | 83 | 65 | 67 | 82 | 33 | 6 |
| あなたは蜃気楼 | 74 | 55 | 66 | 74 | 35 | 2 |
| ロウラヴ | 66 | 48 | 55 | 62 | 43 | 3 |
| It's a small world | 49 | 64 | 30 | 48 | 43 | 3 |
| Vinyl | 76 | 52 | 65 | 76 | 40 | 5 |
| Overflow | 65 | 58 | 48 | 65 | 41 | 3 |
| NIGHT POOL | 34 | 40 | 48 | 76 | 40 | 2 |
| 白日 | 63 | 42 | 62 | 74 | 56 | 6 |
| Slumberland | 83 | 35 | 82 | 86 | 34 | 6 |
| Vivid Red | 77 | 53 | 62 | 72 | 34 | 3 |
| Hitman | 41 | 38 | 45 | 42 | 45 | 5 |
| The hole | 27 | 18 | 62 | 42 | 58 | 5 |
| Don't Stop the Clocks | 26 | 50 | 25 | 25 | 55 | 2 |
| McDonald Romance | 33 | 64 | 23 | 30 | 60 | 4 |
| Bedtown | 41 | 55 | 35 | 38 | 46 | 2 |
| Tokyo Rendez-Vous | 83 | 48 | 74 | 85 | 42 | 6 |
| Prayer X | 58 | 30 | 70 | 62 | 50 | 6 |
| Flash!!! | 94 | 67 | 95 | 94 | 55 | 7 |
| Teenager Forever | 89 | 89 | 58 | 88 | 71 | 6 |
| 傘 | 53 | 31 | 50 | 58 | 52 | 4 |
| サマーレイン・ダイバー | 34 | 55 | 30 | 65 | 89 | 4 |
| どろん | 88 | 45 | 90 | 91 | 36 | 4 |
| ユーモア | 52 | 64 | 28 | 55 | 45 | 3 |
| 破裂 | 33 | 28 | 52 | 28 | 50 | 3 |
| 三文小説 | 51 | 48 | 60 | 82 | 70 | 4 |
| 千両役者 | 93 | 60 | 92 | 92 | 44 | 4 |
| 泡 | 36 | 30 | 46 | 64 | 53 | 3 |
| BOY | 67 | 90 | 25 | 65 | 55 | 4 |
| 一途 | 95 | 38 | 97 | 88 | 43 | 5 |
| カメレオン | 47 | 38 | 54 | 52 | 57 | 3 |
| 雨燦々 | 62 | 86 | 25 | 74 | 68 | 4 |
| 逆夢 | 59 | 50 | 50 | 80 | 64 | 3 |
| STARDOM | 88 | 80 | 63 | 92 | 65 | 3 |
| 小さな惑星 | 61 | 72 | 30 | 60 | 46 | 1 |
| 壇上 | 29 | 55 | 38 | 30 | 71 | 1 |
| SPECIALZ | 88 | 25 | 94 | 90 | 38 | 2 |
| 硝子窓 | 51 | 35 | 56 | 65 | 55 | 2 |
| 2 Μ Ο Я Ο | 48 | 58 | 28 | 52 | 52 | 1 |
| ):阿修羅:( | 92 | 45 | 95 | 96 | 39 | 2 |
| IKAROS | 39 | 40 | 35 | 50 | 56 | 1 |
| ねっこ | 44 | 55 | 40 | 64 | 66 | 1 |
| MASCARA | 51 | 40 | 46 | 58 | 60 | 1 |

## 곡별 음악 자료와 기본값

아래 다섯 숫자는 배치 보정 전의 음악 기본값이며 순서는 에너지 / 밝기 / 긴장 / 밀도 / 마무리입니다. 출처의 숫자를 옮긴 것이 아닙니다.

### 飛行艇

장르·스타일: 앤섬 록. 확인된 악기·음색: 일렉트릭 기타 · 베이스 · 드럼.

2022 라이브의 무거운 기타·베이스 리프를 반영해 에너지와 밀도를 높게 둠.

주관적 음악 기본값: **95 / 72 / 80 / 90 / 70**. [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### Sorrows

장르·스타일: 팝 록 · 펑크. 확인된 악기·음색: 와우 기타 · 슬랩 베이스.

2022 라이브의 빠른 커팅과 슬랩을 반영해 높은 추진력으로 설정.

주관적 음악 기본값: **85 / 65 / 67 / 82 / 38**. [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### あなたは蜃気楼

장르·스타일: 가요 디스코 · 얼터너티브 팝. 확인된 악기·음색: 곡 단위 확인 자료 없음.

공연 리뷰의 가요 디스코·요염한 분위기를 반영. 곡별 악기는 자료에서 확정하지 않음.

주관적 음악 기본값: **76 / 55 / 66 / 74 / 35**. [우타넷 · 2019 공연의 곡별 스타일 리뷰](https://sp.uta-net.com/report/report.php?id=322091) · [음악 나탈리 · 2019 AW 공연 리뷰](https://natalie.mu/music/news/357172)

### ロウラヴ

장르·스타일: 얼터너티브 팝 · 재즈 영향. 확인된 악기·음색: 곡 단위 확인 자료 없음.

대담의 복합 화성 언급과 2025 라이브의 나른한 인상을 반영. 악기는 미확정.

주관적 음악 기본값: **65 / 48 / 55 / 62 / 45**. [Spincoaster · 常田大希 × 小原綾斗 대담](https://spincoaster.com/spin-discovery-vol-05-cross-talk-tempalay-x-king-gnu) · [음악 나탈리 · 2025 CLUB GNU 공연 리뷰](https://natalie.mu/music/news/619979)

### It's a small world

장르·스타일: 펑크 · 팝. 확인된 악기·음색: Acoustasonic 기타 · 목금 계열 건반 음색.

2022의 기타와 2019의 장난스러운 건반 음색을 근거로 중저 에너지·밝은 색채를 설정.

주관적 음악 기본값: **48 / 64 / 30 / 48 / 52**. [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/) · [음악 나탈리 · 2019 AW 공연 리뷰](https://natalie.mu/music/news/357172)

### Vinyl

장르·스타일: 힙합 그루브 · 얼터너티브 록. 확인된 악기·음색: 기타 · 베이스.

리뷰의 힙합 리듬과 기타, 라이브의 움직이는 베이스를 반영해 중고 에너지로 설정.

주관적 음악 기본값: **78 / 52 / 65 / 76 / 50**. [우타넷 · 2019 공연의 곡별 스타일 리뷰](https://sp.uta-net.com/report/report.php?id=322091) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### Overflow

장르·스타일: 팝 · 소울 영향. 확인된 악기·음색: 곡 단위 확인 자료 없음.

2019 공연에서 끊김 없는 보컬 전개가 강조됨. 장르 태그는 편집 해석, 악기 목록은 미확정.

주관적 음악 기본값: **67 / 58 / 48 / 65 / 48**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882)

### NIGHT POOL

장르·스타일: 사이키델릭 · 슈게이즈적 라이브. 확인된 악기·음색: 왜곡된 Acoustasonic 기타 · 신스 베이스.

2019의 부유하는 저음과 2022의 소리 벽을 반영. 느슨한 흐름에도 밀도는 높게 설정.

주관적 음악 기본값: **32 / 40 / 48 / 76 / 45**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### 白日

장르·스타일: 팝 발라드 · 소울 영향. 확인된 악기·음색: 기타 · 보컬.

2019 리뷰의 섬세한 도입과 후반 밴드 고조, 2024 기타 솔로를 반영.

주관적 음악 기본값: **65 / 42 / 62 / 74 / 76**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### Slumberland

장르·스타일: 얼터너티브 록 · 샘플링. 확인된 악기·음색: 샘플링 보이스 · 확성기 처리 보컬.

2024 라이브의 반복 샘플과 선동적인 보컬을 반영해 긴장·에너지를 높임.

주관적 음악 기본값: **88 / 35 / 82 / 86 / 40**. [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### Vivid Red

장르·스타일: 재즈 기반 업템포. 확인된 악기·음색: 건반 리프 · 베이스 · 심벌.

2019 라이브의 재즈적 건반·세밀한 리듬을 반영. 발매 스튜디오 버전으로 일반화하지 않음.

주관적 음악 기본값: **82 / 53 / 62 / 72 / 35**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882)

### Hitman

장르·스타일: 소울 · 재즈 영향. 확인된 악기·음색: 오르간 계열 건반 · 베이스.

2019 오르간과 2022의 음수 적은 편곡을 반영해 에너지·밀도를 낮춤.

주관적 음악 기본값: **40 / 38 / 45 / 42 / 58**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### The hole

장르·스타일: 피아노 발라드. 확인된 악기·음색: 피아노 · 드럼 · 신스 베이스.

2025 라이브의 절제된 반주와 무거운 저음. 에너지는 낮지만 감정적 긴장은 높게 설정.

주관적 음악 기본값: **24 / 18 / 62 / 42 / 82**. [음악 나탈리 · 2025 CLUB GNU 공연 리뷰](https://natalie.mu/music/news/619979) · [음악 나탈리 · 2022 도쿄돔 공연 리뷰](https://natalie.mu/music/news/502139)

### Don't Stop the Clocks

장르·스타일: 어쿠스틱 팝. 확인된 악기·음색: 기타 · 콘트라베이스 · 카혼.

2019 어쿠스틱 구간의 편성을 참고해 낮은 밀도·에너지를 부여. 해당 공연 편곡 기준.

주관적 음악 기본값: **22 / 50 / 25 / 25 / 72**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882)

### McDonald Romance

장르·스타일: 어쿠스틱 팝 · 소울. 확인된 악기·음색: 기타 · 콘트라베이스 · 카혼.

2019 어쿠스틱 편곡의 단순한 음색과 합창을 반영해 따뜻하고 여유 있게 설정.

주관적 음악 기본값: **28 / 64 / 23 / 30 / 74**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882)

### Bedtown

장르·스타일: 어쿠스틱 팝 편곡. 확인된 악기·음색: 기타 · 콘트라베이스 · 카혼.

2019 어쿠스틱 편성과 2025의 소박한 합주를 참고. 원곡보다 공연 편곡에 가까운 초깃값.

주관적 음악 기본값: **38 / 55 / 35 / 38 / 55**. [rockin'on · 2019 Zepp Tokyo 공연 리뷰](https://rockinon.com/live/detail/190882) · [음악 나탈리 · 2025 CLUB GNU 공연 리뷰](https://natalie.mu/music/news/619979)

### Tokyo Rendez-Vous

장르·스타일: 힙합 록. 확인된 악기·음색: 호른 · 현악.

2023 공연의 호른·현악 확장 편곡과 힙합 록 리뷰를 반영. 악기는 2023 공연 기준.

주관적 음악 기본값: **84 / 48 / 74 / 85 / 50**. [음악 나탈리 · 2023 Nissan Stadium 공연 리뷰](https://natalie.mu/music/news/527459) · [우타넷 · 2019 공연의 곡별 스타일 리뷰](https://sp.uta-net.com/report/report.php?id=322091)

### Prayer X

장르·스타일: 얼터너티브 팝 · 무거운 그루브. 확인된 악기·음색: 기타.

2020의 무거운 리듬과 2022 기타 커팅을 반영. 밝기보다 긴장에 무게를 둠.

주관적 음악 기본값: **56 / 30 / 70 / 62 / 68**. [rockin'on · 2020 Budokan 공연 리뷰](https://rockinon.com/live/detail/196824) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### Flash!!!

장르·스타일: 펑크 록 · 일렉트로 록. 확인된 악기·음색: 전자음·샘플링 · 드럼 · 슬랩 베이스.

2020의 전자음·무거운 비트와 2022 슬랩을 근거로 에너지·밀도를 높임.

주관적 음악 기본값: **98 / 67 / 95 / 94 / 66**. [rockin'on · 2020 Budokan 공연 리뷰](https://rockinon.com/live/detail/196824) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### Teenager Forever

장르·스타일: 펑크 성향의 팝 록. 확인된 악기·음색: 베이스 · 드럼.

2024 리뷰의 펑크적 질주와 2022 라이브 저음을 반영해 밝고 강한 에너지로 설정.

주관적 음악 기본값: **93 / 89 / 58 / 88 / 82**. [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### 傘

장르·스타일: 멜랑콜릭 팝 · 록. 확인된 악기·음색: 기타.

2020 공연의 두드러진 기타와 앨범 리뷰의 애수를 참고해 밝기를 낮게 설정.

주관적 음악 기본값: **52 / 31 / 50 / 58 / 65**. [rockin'on · 2020 Budokan 공연 리뷰](https://rockinon.com/live/detail/196824) · [rockin'on · CEREMONY 리뷰](https://rockinon.com/news/detail/191821)

### サマーレイン・ダイバー

장르·스타일: 여운형 팝 · 록. 확인된 악기·음색: 보컬.

2022 공연의 길게 남는 마무리와 과거 종료곡 용례를 반영. 악기별 자료는 부족.

주관적 음악 기본값: **30 / 55 / 30 / 65 / 97**. [음악 나탈리 · 2022 도쿄돔 공연 리뷰](https://natalie.mu/music/news/502139)

### どろん

장르·스타일: 펑크 · 하드코어 성향 록. 확인된 악기·음색: 베이스 · 드럼.

2020의 다급한 합주와 2022 리뷰의 펑키·하드코어 성격을 반영.

주관적 음악 기본값: **92 / 45 / 90 / 91 / 40**. [rockin'on · 2020 Budokan 공연 리뷰](https://rockinon.com/live/detail/196824) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/)

### ユーモア

장르·스타일: 팝 · 소울 영향. 확인된 악기·음색: 목금 음색.

리뷰에서 확인한 목금 음색과 내밀한 정서를 참고. 중간 에너지·낮은 자극으로 설정.

주관적 음악 기본값: **52 / 64 / 28 / 55 / 55**. [Real Sound · CEREMONY 음색 분석](https://realsound.jp/2020/12/post-680376.html) · [rockin'on · CEREMONY 리뷰](https://rockinon.com/news/detail/191821)

### 破裂

장르·스타일: 미니멀 기타 발라드. 확인된 악기·음색: 기타 · 보컬.

2022의 기타와 노래 중심 편성을 반영해 낮은 밀도와 내향적 긴장으로 설정.

주관적 음악 기본값: **28 / 28 / 52 / 28 / 65**. [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/) · [음악 나탈리 · 2022 도쿄돔 공연 리뷰](https://natalie.mu/music/news/502139)

### 三文小説

장르·스타일: 오케스트럴 발라드. 확인된 악기·음색: 피아노 · 오케스트레이션 · 드럼.

장엄한 관현악과 후렴 드럼을 반영. 낮은 템포감과 높은 편곡 밀도를 분리.

주관적 음악 기본값: **50 / 48 / 60 / 82 / 90**. [Real Sound · 三文小説 / 千両役者 리뷰](https://realsound.jp/2020/12/post-680376_2.html) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### 千両役者

장르·스타일: 믹스처 록 · 디지털 록 편곡. 확인된 악기·음색: 베이스 · 드럼·전자 비트.

원곡의 공격성과 TGU 라이브 재편곡의 무거운 비트를 함께 참고.

주관적 음악 기본값: **98 / 60 / 92 / 92 / 45**. [Real Sound · 三文小説 / 千両役者 리뷰](https://realsound.jp/2020/12/post-680376_2.html) · [Fender · 2022 도쿄돔 악기·연주 보고](https://fendernews.jp/kinggnu-live-at-tokyodome/) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### 泡

장르·스타일: 네오소울 · 앰비언트 성향. 확인된 악기·음색: 곡 단위 확인 자료 없음.

TGU 리뷰의 네오소울 리듬과 2023 공연의 앰비언트 인상을 반영. 개별 악기 미확정.

주관적 음악 기본값: **34 / 30 / 46 / 64 / 70**. [Real Sound · TGU 곡별 리듬·장르 해설](https://realsound.jp/2023/12/post-1525814_2.html) · [음악 나탈리 · 2023 Nissan Stadium 공연 리뷰](https://natalie.mu/music/news/527459)

### BOY

장르·스타일: 클래식 · 네오소울 · 펑크 팝. 확인된 악기·음색: 기타.

리스아니의 경쾌한 팝·장르 혼합과 2024 기타 솔로를 참고해 밝기를 높임.

주관적 음악 기본값: **67 / 90 / 25 / 65 / 70**. [리스아니 · BOY 장르·멜로디 리뷰](https://www.lisani.jp/0000183456/) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### 一途

장르·스타일: 고속 기타 록. 확인된 악기·음색: 기타 커팅 · 드럼.

리뷰의 멈추지 않는 빠른 전개와 날카로운 기타를 반영. 높은 에너지가 높은 밝기를 뜻하지 않음.

주관적 음악 기본값: **99 / 38 / 97 / 88 / 45**. [Real Sound · 一途 / 逆夢 리뷰](https://realsound.jp/2021/12/post-934611_2.html) · [Real Sound · 一途 드럼과 리듬 섹션 리뷰](https://realsound.jp/2022/01/post-945767.html)

### カメレオン

장르·스타일: 감상적 팝 발라드. 확인된 악기·음색: 피아노 · 보코더 처리 보컬.

2024 라이브의 피아노·보코더와 2023 발라드 용례를 참고. CHAMELEON과 제목 통합.

주관적 음악 기본값: **46 / 38 / 54 / 52 / 78**. [Billboard Japan · 2024 Tokyo Dome 리뷰](https://www.billboard-japan.com/d_news/detail/136085/2) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/) · [음악 나탈리 · 2023 Nissan Stadium 공연 리뷰](https://natalie.mu/music/news/527459)

### 雨燦々

장르·스타일: 스트링 팝 · 미들 발라드. 확인된 악기·음색: 바이올린 · 첼로 · 오르간 · 기타 · 코러스.

리뷰의 부드러운 현악·오르간과 포근한 편곡을 반영해 밝기와 마무리 기본값을 높임.

주관적 음악 기본값: **62 / 86 / 25 / 74 / 89**. [rockin'on · 雨燦々 리뷰](https://rockinon.com/disc/detail/203379)

### 逆夢

장르·스타일: 오케스트럴 발라드 · 힙합 그루브. 확인된 악기·음색: 현악 · 피아노 · 기타.

피치카토와 피아노·현악의 종결감을 반영. 풍성한 편곡이므로 밀도는 높게 설정.

주관적 음악 기본값: **58 / 50 / 50 / 80 / 91**. [Real Sound · 逆夢 현악·피아노 분석](https://realsound.jp/2022/01/post-942521_2.html) · [Real Sound · 一途 / 逆夢 리뷰](https://realsound.jp/2021/12/post-934611_2.html)

### STARDOM

장르·스타일: 앤섬 록. 확인된 악기·음색: 드럼·리듬 중심 합주.

2022 본편 마지막에서의 역동적인 비트와 앤섬 성격을 반영.

주관적 음악 기본값: **91 / 80 / 63 / 92 / 83**. [음악 나탈리 · 2022 도쿄돔 공연 리뷰](https://natalie.mu/music/news/502139)

### 小さな惑星

장르·스타일: 팝 · 록. 확인된 악기·음색: 글로켄 음색.

리뷰가 짚은 글로켄 음색을 참고해 밝은 질감으로 설정. 전체 악기 목록은 아님.

주관적 음악 기본값: **62 / 72 / 30 / 60 / 50**. [Real Sound · CEREMONY 음색 분석](https://realsound.jp/2020/12/post-680376.html)

### 壇上

장르·스타일: 피아노 발라드. 확인된 악기·음색: 피아노 · 보컬.

앨범 리뷰의 피아노 반주·독백적 마무리를 반영해 낮은 에너지와 높은 종결 기본값을 부여.

주관적 음악 기본값: **23 / 55 / 38 / 30 / 96**. [rockin'on · CEREMONY 리뷰](https://rockinon.com/news/detail/191821)

### SPECIALZ

장르·스타일: 얼터너티브 · 일렉트로 록. 확인된 악기·음색: 보컬 · 반복 루프.

TGU 리뷰의 루프 기반 구성과 어두운 전환, 공연 오프닝의 열기를 반영. 루프 악기 원음은 미확정.

주관적 음악 기본값: **92 / 25 / 94 / 90 / 40**. [Real Sound · TGU 곡별 리듬·장르 해설](https://realsound.jp/2023/12/post-1525814_2.html) · [Billboard Japan · 2024 Tokyo Dome 리뷰](https://www.billboard-japan.com/d_news/detail/136085/2) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### 硝子窓

장르·스타일: 시티팝 영향 · 얼터너티브 팝. 확인된 악기·음색: 피아노 · 베이스 · 드럼 · 현악 · 보코더.

2024 공연의 피아노·리듬과 현악·처리 보컬을 반영. 시티팝 태그는 리뷰 설명을 참고.

주관적 음악 기본값: **52 / 35 / 56 / 65 / 72**. [Real Sound · TGU 곡별 리듬·장르 해설](https://realsound.jp/2023/12/post-1525814_2.html) · [Billboard Japan · 2024 Tokyo Dome 리뷰](https://www.billboard-japan.com/d_news/detail/136085/2) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### 2 Μ Ο Я Ο

장르·스타일: 멜로우 팝 · 그루브. 확인된 악기·음색: 드럼 · 보컬.

2024 공연의 여유 있는 흐름과 후반 드럼 고조를 반영. 확인된 일부 편성만 기록.

주관적 음악 기본값: **48 / 58 / 28 / 52 / 62**. [Billboard Japan · 2024 Tokyo Dome 리뷰](https://www.billboard-japan.com/d_news/detail/136085/2) · [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/)

### ):阿修羅:(

장르·스타일: 댄스 · 일렉트로 록. 확인된 악기·음색: 건반 · 기타 · 드럼.

2024의 댄스 비트·건반·기타와 2025 오프닝 폭발력을 반영.

주관적 음악 기본값: **98 / 45 / 95 / 96 / 42**. [THE FIRST TIMES · 2024 Sapporo Dome 리뷰](https://www.thefirsttimes.jp/report/0000401339/) · [음악 나탈리 · 2025 CLUB GNU 공연 리뷰](https://natalie.mu/music/news/619979)

### IKAROS

장르·스타일: 드리미 팝 · R&B 영향. 확인된 악기·음색: 보컬.

2024 공연의 꿈결 같은 분위기와 TGU 리뷰의 영향 관계를 반영. 구체적 반주 악기는 미확정.

주관적 음악 기본값: **36 / 40 / 35 / 50 / 70**. [Billboard Japan · 2024 Tokyo Dome 리뷰](https://www.billboard-japan.com/d_news/detail/136085/2) · [Real Sound · TGU 곡별 리듬·장르 해설](https://realsound.jp/2023/12/post-1525814_2.html)

### ねっこ

장르·스타일: 피아노·스트링 발라드. 확인된 악기·음색: 피아노 · 현악.

멤버 인터뷰에 나온 피아노·현악 도입과 전조를 참고해 정서적 고조·여운을 설정.

주관적 음악 기본값: **42 / 55 / 40 / 64 / 88**. [음악 나탈리 · ねっこ 멤버 인터뷰](https://natalie.mu/music/pp/kinggnu06)

### MASCARA

장르·스타일: 멜로우 팝 · 셀프 커버. 확인된 악기·음색: 보컬.

인터뷰의 부드러운 창법·과열을 피한 온도감을 반영. SixTONES 원곡 악기를 전용하지 않음.

주관적 음악 기본값: **50 / 40 / 46 / 58 / 65**. [음악 나탈리 · MASCARA 셀프 커버 인터뷰](https://natalie.mu/music/pp/kinggnu06/page/2) · [Sony Music · MASCARA 셀프 커버·라이브 발매](https://www.sonymusic.co.jp/artist/kinggnu/info/567342)

## 파일과 갱신

- `data/king_gnu_setlists.json`: 공연 7개의 순서, 원문 표기와 제외 규칙.
- `data/king_gnu_research.json`: 곡별 음악 설명, 출처, 수작업 기본값. 수정은 이 원자료에서 시작.
- `data/king_gnu_profiles.json`: 최종값, 기본값, 출현별 위치, 공연 통계와 출처를 보존한 생성물.
- `data/king_gnu_songs.json`: 기존 SongCreate 형식의 43곡 Seed.
- `python -m scripts.build_king_gnu`: 인터넷 없이 JSON 두 개와 이 문서를 재생성. 실행 DB를 바꾸지 않음.
- `python -m scripts.seed`: 없는 제목·아티스트 조합만 추가. 기존 사용자 편집을 덮어쓰지 않음.

UI에서 바꾼 값은 SQLite에만 저장되며 이 조사 자료를 바꾸지 않습니다. 이미 만든 Playlist도 생성 당시의 값을 유지합니다. 근거 자료는 별도 읽기 전용 `/api/catalog/king-gnu`에서 확인합니다. 가사·음원·이미지와 YouTube 재생 ID는 포함하지 않습니다.
