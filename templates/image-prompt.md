# 생성 입력 작성

이제 전체 프롬프트를 매일 새로 쓰지 않는다. 고정 지시는 `brand/generation.json`에서 읽어 prepare가 조립한다.

1. 2026-10-02는 공식 검증과 일치할 때 `examples/2026-10-02/content.json`과 `scenes.json`을 그대로 사용한다. 다른 날짜는 공식 복음을 확인하고 `templates/content.json`에 짧은 본문을 작성한다.
2. `templates/scenes.json`의 A/B/C 각각에 `scene`과 `scripture_relation`을 작성한다. 인물·행동·구도와 본문의 연결을 구체화한다. scripture_relation에는 강조한 말씀과 연결되는 눈가·입가·시선·자세·손 또는 공간의 관찰 가능한 단서를 적는다. 얼굴이 없는 장면에는 몸짓과 공간의 단서를 쓴다. 화풍과 질감 지시는 넣지 않는다. 원문에 있는 사실과 회화적 해석을 구분한다.
3. `python3 scripts/sanctusars.py prepare job.json content.json scenes.json`을 실행한다.
4. 출력된 준비 폴더의 실제 참조 이미지를 열어 본다. 각 request.json은 내장 imagegen의 입력 객체다. prompt, referenced_image_paths, transparent_background를 그대로 전달한다. 요약·추가·재해석하지 않는다.
5. 실제 이미지가 나온 후 해당 request 파일로 candidate에 등록한다.

A/B/C는 의미가 다른 장면이어야 한다. 이미지 수정 요청은 색감만 바꾸는 경우에도 항상 새 생성으로 처리한다. 장면·시점·표현 지시를 수정하고 prepare로 새 입력을 만든다. 기존 후보를 편집 대상으로 전달하거나 원본 위에 덧칠하지 않는다. 내장 도구에는 현재 공간 참조 두 장만 넣고 실패 후보·오류 확대 캡처는 넣지 않는다. refine 명령과 이미지 편집 기능은 제거했다. 자동 재제작은 후보별 한 번 후 검토하며 남은 한계는 공개한다. 이전 원본과 성공한 후보는 보존하고 사용자 선택·최종 승인으로 간주하지 않는다.
