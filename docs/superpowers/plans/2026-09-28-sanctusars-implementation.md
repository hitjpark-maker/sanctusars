# SanctusArs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, or superpowers:subagent-driven-development if the user chooses delegation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 검증된 날짜별 복음으로 SanctusArs 시안 세 개와 게시물을 만들고 사용자 선택·승인 후 내보내는 Codex 전용 첫 버전.

**Architecture:** Codex가 공식 자료 조회와 내장 이미지 생성을 수행한다. 작은 Python 도구는 날짜·증거 기록·후보·승인 상태와 출력 파일을 관리한다. 도구가 기록의 구조와 일치 여부를 검사하는 것과, Codex가 실제 출처를 읽어 사실을 확인하는 것을 구분한다. 독립 실행형 이미지 생성 API나 외부 AI 서버를 만들지 않는다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, Codex의 웹 조회·내장 이미지 생성, HTML/CSS 카드 템플릿. 별도 프런트엔드 프레임워크와 데이터베이스 없음.

**Spec:** `docs/superpowers/specs/2026-09-28-sanctusars-design.md`

## Global Constraints

- 브랜드는 SanctusArs로 고정한다. AI는 ChatGPT 또는 Codex만 사용한다.
- 기본 날짜는 Asia/Seoul, 기본 전례력은 한국 천주교다. OS 시간대에 의존하지 않는다.
- 복음 검증 보류 상태에서는 이미지와 글을 생성하지 않는다.
- 제작 건마다 이미지 시안 세 개를 실제로 생성하고 사용자가 선택한다.
- 시안 선택과 최종 승인은 별개다. 자동 게시 기능을 만들지 않는다.
- 내장 이미지 생성이 없는 환경에서는 안내 후 중단한다. API 키나 외부 AI로 우회하지 않는다.
- 일일 결과와 원문 자료를 기본 Git 추적에서 제외한다. 코드와 브랜드 자산의 라이선스를 임의로 정하지 않는다.
- 원본 보존, 버전별 수정, 중단 후 재개를 지원한다. 불필요한 추상화와 플러그인 구조는 만들지 않는다.

## Review Focus

1. 미국 현지 날짜와 한국 날짜가 다를 때 ‘오늘’이 틀리는 문제: Task 1에서 고정 UTC 시각으로 검사.
2. URL은 맞지만 본문이 다른 날짜이거나 복음 환호송을 읽은 문제: Task 2에서 불일치와 구역 식별 검사, 실제 출처 수동 대조.
3. 성탄 미사 선택과 같은 날 여러 성인의 혼합: Task 2에서 선택 미확정 거절, Task 3에서 제작 건 격리.
4. 승인 이후 이미지나 본문 파일을 바꾼 문제: Task 3·4에서 파일 내용 해시가 달라지면 내보내기 거절.
5. 경로에 공백·한글, 출력 중단, 한글 글꼴 누락: Task 1에서 원자적 기록, Task 4에서 실제 렌더링과 파일 경로 검사.

## 파일과 책임

- `README.md`: 실행 환경, 최초 clone/이후 pull, 제작 요청과 승인 예시, 한계.
- `AGENTS.md`: 공식 출처 조회, 생성 도구 호출, 사용자 선택·승인 경계, 재개 절차.
- `brand/style.md`: 잠정 스타일과 승인된 기준 작품 기록. 승인 전 확정 브랜드 가이드로 표시하지 않는다.
- `templates/brief.md`: 복음·특별 포스팅의 장면, 묵상과 질문, 검수 양식.
- `templates/card.html`: 같은 그림으로 작품형·말씀카드형을 보여 주는 로컬 HTML/CSS 템플릿.
- `scripts/sanctusars.py`: 기록과 승인 검증, 파일 해시, 조판 템플릿 채우기와 승인 묶음 출력.
- `tests/test_workflow.py`: 표준 라이브러리 unittest 기반 핵심 실패 사례.
- `.gitignore`: output/, 임시 파일, Python 캐시와 비밀정보 제외.
- `output/YYYY-MM-DD/<post_id>/`: 한 제작 건의 기록, 출처 확인 요약, candidates/, revisions/, preview/, export/.

## Task 1: 날짜와 재개 가능한 제작 기록

**Files:** Create `scripts/sanctusars.py`, `tests/test_workflow.py`, `.gitignore`.

**Interfaces:** `resolve_date(value: str, now: datetime) -> str`; `create_job(root: Path, date: str, post_id: str, kind: str) -> Path`; `load_job(path: Path) -> dict`; `save_job(path: Path, data: dict) -> None`.

- [ ] 시간대 인식 datetime을 받는 날짜 테스트를 먼저 작성한다. `resolve_date('오늘', datetime(2026, 9, 28, 16, tzinfo=timezone.utc)) == '2026-09-29'`와 '내일'의 2026-09-30, 명시 날짜 보존, 2026-02-30 거절을 검사한다.
- [ ] `python3 -m unittest discover -s tests -v`를 실행해 새 기능 부재로 실패하는지 확인한다.
- [ ] `zoneinfo.ZoneInfo('Asia/Seoul')`, `date.fromisoformat`으로 구현한다. 시간대 데이터 부재는 OS 시간대로 대체하지 않고 명확한 오류를 낸다.
- [ ] 기록은 schema_version, date, timezone, calendar, post_id, kind, evidence, candidates, selection, final_approval을 가진 JSON으로 둔다. kind는 gospel/occasion, post_id는 경로 구분자를 허용하지 않는 짧은 식별자다. 임시 파일과 `os.replace`로 저장하고 기존 제작 건은 덮어쓰지 않는다.
- [ ] 한글·공백 경로에서 저장·재읽기, 경로 탈출 거절, 기존 기록 보존 테스트를 추가하고 통과시킨다.

## Task 2: 공식 출처를 읽는 절차와 생성 전 검증

**Files:** Modify `scripts/sanctusars.py`, `tests/test_workflow.py`; Create `AGENTS.md`, `templates/brief.md`.

**Interfaces:** `validate_evidence(job: dict) -> list[str]`; 오류 목록이 비어야 생성 가능하다. 입력 evidence는 primary_url, checked_at, body_date, liturgical_day, calendar_url, mass_form, gospel_reference, gospel_section, quotation, crosscheck_url, crosscheck_date, crosscheck_mass_form, crosscheck_reference, occasions, unresolved_choices를 포함한다.

- [ ] 요청·본문·교차 확인 날짜 불일치, 장절 불일치, mass_form 미확정, unresolved_choices가 남음, gospel_section이 복음 환호송인 경우를 모두 거절하는 테스트를 작성한다. 합성 자료를 테스트로 표시하고 공식 검증 완료의 증거로 사용하지 않는다.
- [ ] 테스트 실패 확인 후 일치·필수 필드 검사를 구현하고 테스트를 통과시킨다. URL이나 체크박스만으로 사실의 진실성을 증명한다고 표현하지 않는다.
- [ ] AGENTS.md에 주교회의 해당 날짜 본문 조회, 전례력 대조, 교회 보조 자료 교차 확인, 직접 인용 대조를 순서대로 적는다. 사이트 접근 실패나 선택지 미확정 시 생성 중단을 명시한다. 원문 전체 재배포 대신 필요한 확인 요약과 링크를 기록한다.
- [ ] 공식 전례일·등급·거행일과 선택 가능한 기념일을 구분해 occasions에 기록한다. 복수 성인은 사용자 선택 후 별도 제작 건을 만든다. 전승·생애·도상 상징은 별도 출처를 확인한다.
- [ ] 2026-09-28의 실제 공식 자료로 날짜·루카 9,46-50을 대조한다. 성탄과 성모 승천 대축일은 해당 연도 자료에서 미사 선택지를 직접 확인한다. 접근할 수 없다면 검증 완료로 꾸미지 않고 기록한다.

## Task 3: 실제 시안 세 개와 두 번의 사용자 결정

**Files:** Modify `scripts/sanctusars.py`, `tests/test_workflow.py`, `AGENTS.md`; Create `brand/style.md`.

**Interfaces:** `register_candidate(job_path: Path, label: str, image: Path, prompt: str) -> None`; `select_candidate(job_path: Path, label: str, user_message: str) -> None`; `approve_final(job_path: Path, files: list[Path], user_message: str) -> None`; `verify_approval(job_path: Path) -> list[str]`.

- [ ] 검증 보류 상태의 후보 등록, 파일 없는 후보, 세 후보 준비 전 선택, 선택 없는 최종 승인, 빈 사용자 결정 근거를 거절하는 테스트를 작성한다. gospel과 occasion 두 제작 건의 선택이 서로 영향을 주지 않는지 검사한다.
- [ ] 실패 확인 후 최소 상태 검사를 구현한다. 후보 파일을 버전별로 복사하고 해시와 지시문을 보존한다. PNG/JPEG/WebP 파일 판별과 실제 시각 검토를 구분한다. 같은 파일을 세 후보로 재등록하는 것을 거절한다.
- [ ] AGENTS.md에 내장 이미지 도구로 각각 세 번 생성하는 실행 순서를 적는다. 프롬프트·플레이스홀더를 결과 이미지로 대체하지 않는다. 생성 결과를 프로젝트 안으로 보존하고 세 후보를 표시한 후 사용자 선택을 기다린다. 부분 실패 때 성공한 후보를 유지한다.
- [ ] `brand/style.md`에 신비로운 사실성·붓질·인체·의미 있는 디테일 기준과 첫 스타일 선택/일일 장면 선택의 차이를 기록한다. 선택한 기준 이미지가 없다면 ‘미확정’으로 표시한다.
- [ ] 선택·승인 함수는 사용자 결정 기록 수단일 뿐 본인 인증 장치가 아님을 명시한다. Codex는 명시적인 사용자 메시지 없이 승인 명령을 실행하지 않는다. 승인 파일 해시 변경·누락 시 verify_approval이 오류를 반환하는 테스트를 통과시킨다.

## Task 4: 최종 미리보기와 게시용 묶음

**Files:** Modify `scripts/sanctusars.py`, `tests/test_workflow.py`, `AGENTS.md`; Create `templates/card.html`.

**Interfaces:** `render_preview(job_path: Path, image: Path, content: dict, logo: Path, font: Path) -> Path`; `export_approved(job_path: Path) -> Path`. content는 scripture_quote, reference, meditation, prayer, question, threads_text, blog_text를 갖는다.

- [ ] 미승인 내보내기, 승인 후 파일 변경, 로고·글꼴 누락, HTML 특수문자가 포함된 문구, 다른 제작 건 파일 참조를 검사하는 테스트를 작성하고 실패를 확인한다.
- [ ] HTML 문자열은 `html.escape`로 처리한다. 브랜드 로고와 글꼴은 실제 제공·승인된 로컬 자산만 사용한다. 템플릿에는 성경 인용과 묵상을 구별하고 날짜·전례일·미사·장절·출처를 검토용 정보로 함께 표시한다. 이미지 자체 편집은 내장 이미지 도구, 글자·로고 배치는 조판으로 처리한다.
- [ ] 첫 카드 규격은 1080×1350으로 제안하고 잘림 없이 이미지를 배치한다. 실제 자산과 문구로 사용자에게 보여 준 뒤 확정한다. 브라우저 렌더링 결과를 확인하며, 잘림·한글 대체 문자·글꼴 누락이 있으면 승인 단계로 진행하지 않는다.
- [ ] 실제 이미지 내보내기 기능이 현재 환경에 있는지 확인해 사용하는 방법을 문서화한다. HTML만 출력하고 게시용 PNG가 완성됐다고 주장하지 않는다. 런타임 종속 도구 경로를 저장소에 하드코딩하지 않는다.
- [ ] 이미지·채널별 텍스트·출처 요약의 최종 파일 목록과 해시를 사용자 승인에 연결한다. 승인된 파일만 새 export 디렉터리에 복사하고 테스트를 통과시킨다. 게시 연결·게시 명령은 만들지 않는다.

## Task 5: 재사용 안내와 실제 한 회차 검증

**Files:** Create `README.md`; Modify `AGENTS.md` and implementation files only for proven defects.

- [ ] README에 저장소 복제 → Codex에서 열기 → 내장 이미지 생성 가능 여부 확인 → 날짜 지정 → 세 시안 선택 → 최종 승인 → 수동 게시 순서를 적는다. 실제 GitHub 저장소가 생기기 전에는 가짜 원격 주소를 넣지 않는다.
- [ ] 코드 실행 명령은 argparse의 init/check/select/approve/export로 공개한다. 이미지 생성 자체는 Codex가 담당하며 독립 CLI가 자동 생성한다고 설명하지 않는다. Python 버전, 시간대 데이터, 조판 환경, 자산 준비, 생성 도구 접근 요건을 명시한다.
- [ ] 신비로운 사실적 회화의 첫 세 시안을 실제 생성해 보여 주고 사용자의 선택을 받는다. 선택 없이 이후 단계를 완료했다고 표시하지 않는다. 로고 원본과 글꼴 사용 조건이 확보되지 않으면 해당 조판 단계를 차단 사유로 기록한다.
- [ ] `python3 -m unittest discover -s tests -v`를 실행한다. 실제 한 회차의 웹 검증·생성·선택·조판·최종 승인·출력을 별도로 확인한다. 단위 테스트 통과와 실제 한 회차 완료를 구분해 보고한다.
- [ ] 깨끗한 작업 복사본에서 문서의 명령과 재개 흐름을 확인한다. 불필요한 추상화·외부 AI 호출·게시 경로·비밀정보·미승인 자산이 없는지 변경 전체를 검토한다.
- [ ] 로컬 Git 저장소를 초기화하고 완성·검증한 단계별 변경을 커밋한다. 기존 저장소가 생겼다면 상태를 먼저 확인한다. 공개 라이선스, 자산 배포 권한, 실제 GitHub 대상은 사용자와 확정한 뒤 별도 공개 단계에서 처리하며 이 계획으로 자동 공개하지 않는다.

## 계획 자체 검토 결과

- 사양의 날짜·전례·출처, 특별 포스팅, 내장 생성, 세 후보, 별도 승인, 원본 보존, 출력과 재사용 안내를 각 작업에 배정했다.
- 출처 확인과 화풍 품질은 단위 테스트만으로 증명할 수 없으므로 실제 도구 실행과 사용자 확인을 완료 조건으로 유지했다.
- 로고·서체·대표 작품은 미확정 자산이며 임의 승인하지 않는다. 해당 자산을 요구하지 않는 날짜 검증과 승인 흐름 구현은 먼저 진행할 수 있다.
- 실행 방식과 계획 검토에 대한 사용자 응답을 받은 뒤 구현을 시작한다.
