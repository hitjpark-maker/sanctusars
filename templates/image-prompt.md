# 생성 입력 작성

이제 전체 프롬프트를 매일 새로 쓰지 않는다. 고정 지시는 `brand/references/v5/generation.json`에서 읽어 prepare가 조립한다.

1. 2026-10-06은 공식 검증과 일치할 때 `examples/2026-10-06/content.json`의 짧은 본문을 사용한다. 당시 `scenes.json`은 복제 금지 사례로 읽고 A/B/C의 장면은 새로 설계한다. 다른 날짜는 공식 복음을 확인하고 `templates/content.json`에 짧은 본문을 작성한다.
2. `templates/scenes.json` 최상위의 `character_continuity`에 해당 포스팅의 인물별 외형과 의복 형태·기본 색을 한 번 정한다. 모든 시안에 인물이 없으면 그 사실을 쓴다. A/B/C 각각에는 `scene`, `scripture_relation`, `camera_axis`, `sacred_light`를 작성한다. 공통 인물 설정과 충돌하는 복장을 후보별로 다시 지정하지 않는다. 인물·행동·구도와 본문의 연결을 구체화하고 세 카메라 축을 실제로 다르게 쓴다. scripture_relation에는 강조한 말씀과 연결되는 관찰 가능한 단서를 적는다. 거룩한 인물이 보이면 sacred_light에 머리·옷·손·곁의 공기 중 한 곳의 은은한 빛을 지정하고, 보이지 않을 때만 `none`을 쓴다. 전체 화풍과 질감 지시는 넣지 않는다. 원문에 있는 사실과 회화적 해석을 구분한다.
3. `python3 scripts/sanctusars.py prepare job.json content.json scenes.json`을 실행한다.
4. 출력된 준비 폴더의 실제 참조 이미지를 열어 본다. 각 request.json은 내장 imagegen의 입력 객체다. prompt, referenced_image_paths, transparent_background를 그대로 전달한다. 요약·추가·재해석하지 않는다.
5. 실제 이미지가 나온 후 해당 request 파일로 candidate에 등록한다.

같은 인물의 보이는 외형과 복장은 세 후보에서 일치시킨다. 인물이나 소품을 생략한 후보에 연속성을 위해 추가하지 않는다. 공통 설정을 바꾸면 세 입력이 모두 달라지므로 기존 후보를 다시 생성해야 한다. 이전 scenes 파일을 새 제작에 쓸 때는 character_continuity를 먼저 작성한다. 보존된 과거 제작 기록은 덮어쓰지 않는다.

A/B/C는 의미가 다른 장면이어야 한다. 이미지 수정 요청은 색감만 바꾸는 경우에도 항상 새 생성으로 처리한다. 장면·시점·표현 지시를 수정하고 prepare로 새 입력을 만든다. 기존 후보를 편집 대상으로 전달하거나 원본 위에 덧칠하지 않는다. 내장 도구에는 현재 공간 참조 두 장만 넣고 실패 후보·오류 확대 캡처는 넣지 않는다. refine 명령과 이미지 편집 기능은 제거했다. 자동 재제작은 후보별 한 번 후 검토하며 남은 한계는 공개한다. 이전 원본과 성공한 후보는 보존하고 사용자 선택·최종 승인으로 간주하지 않는다.
