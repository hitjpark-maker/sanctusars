# SanctusArs

매일의 복음을 성화와 묵상으로, 함께 나누는 신앙 문화로.

Codex에서 사용하는 **SanctusArs 전용 제작 프로젝트**다. 공식 전례 자료를 확인하고 내장 이미지 생성으로 시안 세 개를 만든다. 사용자가 고른 그림에 글과 로고를 조판하고, 최종 승인된 파일을 출력한다. 외부 AI 서비스와 자동 게시 기능은 없다.

## 시작하기

1. 처음에는 이 저장소를 clone하거나 내려받는다. 이후 업데이트는 `git pull`로 받는다. 현재는 로컬 저장소이며 GitHub 원격은 아직 연결하지 않았다.
2. Python **3.11 이상**과 `Asia/Seoul` 시간대 데이터가 있는 환경에서 폴더를 Codex로 연다. `python3 --version`으로 확인한다. 이 프로젝트의 Python 코드는 표준 라이브러리만 사용한다.
3. Codex에 **웹 조회와 내장 이미지 생성 도구**가 제공되어야 한다. 생성 도구가 없으면 시작 시 안내하고 멈춘다. 저장소 복제만으로 기능 접근 권한이 생기지는 않는다. API 키·외부 AI 대체 경로는 없다.
4. 다음처럼 요청한다.

> 2026-10-01의 SanctusArs 포스팅을 만들어줘. 공식 복음을 확인하고 특별 기념일도 확인해줘.

날짜를 생략하면 한국 날짜를 먼저 확정한다. 로컬 PC의 미국 날짜를 그대로 쓰지 않는다. 여러 미사 양식 또는 특별 성인 후보가 있으면 선택을 요청한다.

## 사용 흐름

**날짜·공식 복음 확인 → 시안 A/B/C → 사용자 선택 → 문구·카드 미리보기 → 최종 승인 → 파일 출력**

- ‘B로 해줘’는 시안 선택이다. 최종 게시물 승인이 아니다.
- 이미지·글·날짜가 바뀌면 다시 검토한다. 승인 이후 파일 변조도 해시 검사로 막는다.
- 같은 날 특별 포스팅은 별도 제작 건이다. 매일 복음의 이미지나 승인 상태를 덮어쓰지 않는다.
- 댓글·포스팅을 대신 게시하지 않는다. 승인된 파일을 사용자가 직접 게시한다.
- 코드의 자료 일치 검사와 Codex가 실제 원문을 읽는 검토는 다르다. JSON에 URL을 써 넣는 것만으로 진실성이 보증되지 않는다.

## 카드에 필요한 자산

- 기준 화풍: 사용자가 선택한 **B — 깊은 명암과 신비로움**. `brand/style.md`와 `brand/reference-b.png` 참고.
- 공식 로고: 사용자가 제공하는 PNG/JPEG/WebP 원본. 임의 로고로 대체하지 않는다. SVG는 안전하게 래스터로 내보낸 공식 버전을 제공한다.
- 한글 글꼴: 사용 및 배포 조건을 확인한 TTF/OTF/WOFF/WOFF2. 본문은 실제 브라우저에서 확인해야 한다.

로고·글꼴이 없으면 시안까지 만들 수 있지만 최종 브랜드 카드 제작은 보류한다. 제공 전 임의의 상업적 사용·재배포 허락을 가정하지 않는다. 로고와 글꼴은 자산 승인이 끝난 뒤 `brand/`에 둔다.

## 파일과 실행 명령

일일 결과는 `output/YYYY-MM-DD/<post_id>/`에 보관하고 Git에서 제외한다. 같은 제작 건을 동시에 여러 프로세스가 수정하지 않는다. 새 세션에서는 `status`를 확인해 이어간다.

아래 명령은 Codex가 실행하거나 운영자가 사용할 수 있다. `job.json` 대신 실제 경로를 넣는다. `select`와 `approve`는 사용자의 실제 선택을 기록하기 위한 명령이며 인증 시스템이 아니다.

```sh
python3 scripts/sanctusars.py init 2026-10-01
python3 scripts/sanctusars.py init 2026-10-01 --id saint-therese --kind occasion
python3 scripts/sanctusars.py evidence output/2026-10-01/gospel/job.json evidence.json
python3 scripts/sanctusars.py check output/2026-10-01/gospel/job.json
python3 scripts/sanctusars.py status output/2026-10-01/gospel/job.json
```

`templates/evidence.json`을 실제 조회 결과로 채운 뒤 등록한다. 빈 값과 모순은 차단된다. 증거를 수정하면 시안의 검증 문맥도 무효화되므로 다시 검토·생성해야 한다.

```sh
python3 scripts/sanctusars.py candidate job.json A generated-a.png --prompt-file prompt-a.txt
# B, C도 각각 내장 이미지 도구로 생성한 실제 파일로 등록
python3 scripts/sanctusars.py select job.json B --message '사용자의 실제 선택 메시지'
python3 scripts/sanctusars.py preview job.json content.json --logo brand/logo.png --font brand/font.otf
```

`templates/content.json`을 채운다. `card_kind=scripture`이면 검증된 복음 발췌만, `meditation`이면 창작 묵상 문구를 넣는다. 최종 미리보기 HTML에는 글꼴·이미지가 내장되어 외부 서버에 보내지 않는다. 최신 브라우저에서 열어 두 다운로드 버튼으로 **1080×1350 PNG**를 받는다. 렌더링 오류가 표시되면 먼저 해결한다.

```sh
python3 scripts/sanctusars.py rendered job.json artwork.png card.png --review '한글·로고·잘림·원본 일치 실제 확인'
# 이미지 두 개와 Threads/블로그 글 전체를 사용자에게 보여 준 뒤에만 실행
python3 scripts/sanctusars.py approve job.json --message '사용자의 실제 최종 승인 메시지'
python3 scripts/sanctusars.py export job.json
```

`rendered`는 PNG 크기와 이전 파일의 변경 여부를 검사한다. 파일이 정확한 화면을 그렸는지, 이미지에 결함이 없는지는 실제 시각 검토가 필요하다. 출력 묶음에는 작품형·말씀카드형 PNG, 채널별 텍스트, 문구·출처·승인 기록이 들어간다. 기존 결과는 보존한다.

## 검증

```sh
python3 -m unittest discover -s tests -v
```

테스트의 가상 복음 자료와 작은 이미지·가짜 글꼴은 단위 테스트 전용이다. 실제 이미지 생성이나 신학적 정확성을 증명하지 않는다. 실제 자료 조회·생성·조판 검증 현황은 `docs/superpowers/implementation-log.md`에 기록한다.

## 범위와 배포

이것은 **Codex가 실행하는 제작 절차 + 로컬 기록·조판 도구**다. Python 명령 하나가 Codex 내장 이미지 도구를 직접 호출하는 독립 AI 프로그램은 아니다. ChatGPT 단독 자동 실행과 모든 Codex 배포 환경의 호환성을 보장하지 않는다.

브랜드와 콘텐츠는 SanctusArs로 고정된다. 공개 코드 라이선스와 브랜드·이미지의 재배포 조건은 아직 결정되지 않았다. 현재 명시적인 오픈소스 라이선스를 부여한 상태로 해석하지 않는다. 공식 전례 자료는 출처를 연결하고 전체 본문을 Git에 일괄 수록하지 않는다.
