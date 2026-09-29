# SanctusArs

매일의 복음을 성화와 묵상으로, 함께 나누는 신앙 문화로.

Codex에서 사용하는 **SanctusArs 전용 제작 프로젝트**다. 공식 전례 자료를 확인하고 내장 이미지 생성으로 시안 세 개를 만든다. 그림과 Threads·네이버 블로그 글을 함께 제시하고 사용자가 검토한다. 말씀카드 조판은 별도 선택 과정이다. 외부 AI 서비스와 자동 게시 기능은 없다.

## 시작하기

1. [GitHub 저장소](https://github.com/hitjpark-maker/sanctusars)를 처음에는 아래 명령으로 받는다. 이후 업데이트는 폴더 안에서 `git pull`로 받는다.

   ```sh
   git clone https://github.com/hitjpark-maker/sanctusars.git
   cd sanctusars
   ```
2. Python **3.11 이상**과 `Asia/Seoul` 시간대 데이터가 있는 환경에서 폴더를 Codex로 연다. `python3 --version`으로 확인한다. 이 프로젝트의 Python 코드는 표준 라이브러리만 사용한다.
3. Codex에 **웹 조회와 내장 이미지 생성 도구**가 제공되어야 한다. 생성 도구가 없으면 시작 시 안내하고 멈춘다. 저장소 복제만으로 기능 접근 권한이 생기지는 않는다. API 키·외부 AI 대체 경로는 없다.
4. 다음처럼 요청한다.

> 오늘 복음 포스팅 만들어줘.

**사용자는 날짜만 요청하면 된다.** 날짜를 지정하려면 “2026년 10월 1일 복음 포스팅 만들어줘”라고 한다. Codex가 공식 복음 확인, 짧은 글 작성, 고정 생성 입력 준비, 실제 이미지 세 장 생성과 검토를 진행한다. 사용자가 프롬프트나 참조 파일을 골라 전달할 필요는 없다.

**기본은 복음 포스팅 한 건과 그림 세 장**이다. 전례일은 매번 확인하되 축일 특별 포스팅은 요청받을 때만 별도로 세 장을 만든다. [최신 글과 그림 예시](examples/2026-10-02/README.md)에서 기준을 볼 수 있다.

**2026년 10월 2일 제작:** 공식 복음이 예시의 마태 18,1-5.10과 일치하면 동봉된 `examples/2026-10-02/content.json`과 `scenes.json`을 그대로 prepare에 사용한다. 두 채널 본문은 같은 249자이며 생성 지시와 v3 참조는 고정된다. 실제 새 그림 세 장을 만들고 동봉된 기준과 비교한다. 예시 그림을 새 생성 결과인 것처럼 제공하지 않는다. 새 생성의 픽셀 단위 동일성은 보장하지 않으며, 예시 자체가 필요하면 동봉 원본 세 장을 그대로 받을 수 있다.

날짜를 생략하면 한국 날짜를 먼저 확정한다. 로컬 PC의 미국 날짜를 그대로 쓰지 않는다. 여러 미사 양식 또는 특별 성인 후보가 있으면 선택을 요청한다.

## 사용 흐름

**날짜·공식 복음 확인 → 포스팅 글과 그림 A/B/C → 사용자 선택·검토**

말씀카드를 요청하면 이어서 **문구·카드 미리보기 → 최종 승인 → 파일 출력**을 진행한다. 아래 `preview` 이후 명령은 카드 제작 경로다. 로고와 서체 없이도 기본 그림·글 시안 제작은 가능하다.

- ‘B로 해줘’는 시안 선택이다. 최종 게시물 승인이 아니다.
- `brand/editorial.md`의 짧은 본문과 그림 세 개를 함께 검토한다. 기본은 Threads·블로그 공통 본문이며 긴 블로그 해설은 따로 요청할 때만 쓴다. 끝 질문은 문맥에 자연스러울 때만 사용하며, `question`은 생략하거나 빈 문자열로 둘 수 있다. 해시태그는 넣지 않는다.
- 이미지·글·날짜가 바뀌면 다시 검토한다. 승인 이후 파일 변조도 해시 검사로 막는다.
- 같은 날 특별 포스팅은 별도 제작 건이다. 매일 복음의 이미지나 승인 상태를 덮어쓰지 않는다.
- 댓글·포스팅을 대신 게시하지 않는다. 승인된 파일을 사용자가 직접 게시한다.
- 코드의 자료 일치 검사와 Codex가 실제 원문을 읽는 검토는 다르다. JSON에 URL을 써 넣는 것만으로 진실성이 보증되지 않는다.

## 카드에 필요한 자산

- 기준 화풍: `brand/references/v3/`의 사용자 지정 두 참조로 현대적 색면·생략된 공간·인물 관계를 유지한다. 최신 요청에 따라 **중성에 가까운 은은한 온기**를 사용하며 고정 지시로 이 균형을 적용한다. 참조 원본의 차가운 색감은 복제하지 않는다. `brand/generation.json`에 후보별 참조 순서와 고정 지시가 있다. `brand/style.md`와 `brand/references/v3/README.md`를 따른다. v1·v2는 이력으로 보존한다.
- 공식 로고: 사용자가 제공하는 PNG/JPEG/WebP 원본. 임의 로고로 대체하지 않는다. SVG는 안전하게 래스터로 내보낸 공식 버전을 제공한다.
- 한글 글꼴: 사용자 지정 **Pretendard(프리텐다드)**. 실제 파일과 사용·배포 조건을 준비한다. 지원 형식은 TTF/OTF/WOFF/WOFF2이며 본문은 실제 브라우저에서 확인해야 한다.

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
python3 scripts/sanctusars.py prepare job.json content.json scenes.json
# 출력된 prepared/v-N의 A/B/C-request.json을 Codex가 내장 이미지 도구에 그대로 전달
python3 scripts/sanctusars.py candidate job.json A generated-a.png --request-file prepared/v-N/A-request.json
# B, C도 실제 생성한 뒤 해당 request 파일로 등록
# 수정 요청은 scenes를 다시 설계하고 prepare 후 해당 후보를 새로 생성
python3 scripts/sanctusars.py select job.json B --message '사용자의 실제 선택 메시지'
python3 scripts/sanctusars.py preview job.json content.json --logo brand/logo.png --font brand/font.otf
```

`templates/content.json`과 `templates/scenes.json`은 Codex가 채운다. prepare는 글 길이·공통 본문·인용 표기를 검사하고, `brand/generation.json`의 고정 지시와 확정 참조를 결합한다. 준비 폴더에는 실제 도구 입력, 글, 참조 사본을 보존한다. 신규 제작은 준비 요청 없이 후보를 등록할 수 없다. 이 명령이 이미지를 생성하는 것은 아니며 실제 내장 도구 호출은 Codex가 담당한다. `card_kind=scripture`이면 검증된 복음 발췌만, `meditation`이면 창작 묵상 문구를 넣는다. 최종 미리보기 HTML에는 글꼴·이미지가 내장되어 외부 서버에 보내지 않는다. 최신 브라우저에서 열어 두 다운로드 버튼으로 **1080×1350 PNG**를 받는다. 렌더링 오류가 표시되면 먼저 해결한다.

이미지 수정 요청은 색감만 바꾸는 경우에도 항상 새 생성으로 처리한다. 장면·시점·표현 지시를 수정하고 prepare로 새 입력을 만든다. 기존 후보를 편집 대상으로 전달하거나 원본 위에 덧칠하지 않는다. 내장 도구에는 현재 공간 참조 두 장만 넣고 실패 후보·오류 확대 캡처는 넣지 않는다. refine 명령과 이미지 편집 기능은 제거했다. 자동 재제작은 후보별 한 번 후 검토하며 남은 한계는 공개한다. 이전 원본과 성공한 후보는 보존하고 사용자 선택·최종 승인으로 간주하지 않는다.

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

## Plus 지원과 재현성

2026년 9월 29일 공식 문서 확인 기준, 월 20달러 ChatGPT Plus에는 Codex가 포함된다. [공식 요금 문서](https://learn.chatgpt.com/docs/pricing)와 [내장 이미지 생성 문서](https://learn.chatgpt.com/docs/image-generation)에 따르면 내장 이미지 생성은 `gpt-image-2`를 사용하고 일반 Codex 사용량에 포함된다. 공식 문서는 Plus 전용의 저품질 이미지 모델을 명시하지 않는다. 이것이 계정 간 동일한 품질을 보장한다는 뜻은 아니다.

[모델 안내](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex)에 따르면 Plus에서도 Astra를 사용할 수 있으나 포함 사용량이 제한된다. 계정의 실제 모델 선택과 추론 설정, 내장 이미지 도구 제공 여부를 확인한다. 이 저장소는 생성 모델 버전을 강제하거나 구독 권한을 제공하지 않는다. 외부 API로 전환하지 않는다.

이미지 생성은 이미지가 없는 유사 작업보다 포함 사용량을 평균 3배에서 5배 빠르게 소모할 수 있다. 기본 하루 세 장이면 28일은 84장, 30일은 90장, 31일은 93장이다. 특별 포스팅과 수정 생성은 여기에 추가된다. 이는 필요한 이미지 수이지 Plus가 보장하는 월간 제공량이 아니다. **월 20달러 안에서 한 달 내내 이 작업량을 소화할 수 있는지는 미검증이다.** 실제 한도는 계정에서 확인한다. 한도에 닿으면 진행 상태를 보존하고 멈춘다. 외부 API 호출, 추가 결제, 품질을 낮추는 모델 변경을 자동으로 하지 않는다.

**재현 실패와 수정:** 다른 사용자 환경에서 글 분량과 그림 스타일이 기준을 벗어났다. 지침만 보강한 뒤에도 반복되어, 생성 입력을 실행 모델이 매번 새로 쓰던 경로를 prepare로 교체했다. 고정 프롬프트·참조 조합과 짧은 공통 본문 검사는 코드에서 처리한다. 생성 모델의 출력 변동이나 미적 품질까지 결정적으로 보장하는 기능은 아니다. 실제 검증 범위는 구현 기록에 명시하며 코드 테스트와 화풍 재현을 구분한다.

현재는 공식 문서로 기능 지원을 확인한 단계다. 별도의 Plus 계정에서 새로 복제한 저장소만으로 제작하는 재현성 시험은 아직 수행하지 않았다. 실사용 검증에서는 기존 대화 없이 참조 이미지·지침만 읽고 같은 날짜 한 건과 다른 날짜 한 건을 제작하여 글과 복음의 일치, 화풍, 얼굴·손, 수정 횟수와 사용량을 비교해야 한다. 사용 가능 여부, 일관된 품질, 비용 내 지속 운영을 각각 확인한다.

현재 참조 두 장과 원래 생성 프롬프트는 `brand/references/v3/`에, 이전 여섯 장은 `brand/references/v1/`에 보존한다. 원래 프롬프트는 출처 기록이며 최신 색감 지시를 덮어쓰지 않는다.

## 범위와 배포

이것은 **Codex가 실행하는 제작 절차 + 로컬 기록·조판 도구**다. Python 명령 하나가 Codex 내장 이미지 도구를 직접 호출하는 독립 AI 프로그램은 아니다. ChatGPT 단독 자동 실행과 모든 Codex 배포 환경의 호환성을 보장하지 않는다.

브랜드와 콘텐츠는 SanctusArs로 고정된다. 코드·템플릿·직접 작성한 문서는 [MIT 라이선스](LICENSE)로 제공한다. 포함된 참조 이미지는 이 SanctusArs 제작 시스템의 사용·공유를 위해 함께 제공한다. 브랜드명에 대한 권리나 제삼자 자료의 권리를 양도한다는 뜻은 아니다. 성경 인용과 공식 전례 자료는 해당 출처의 권리를 따르며 전체 본문을 Git에 일괄 수록하지 않는다. Pretendard와 공식 로고 파일은 포함하지 않는다.
