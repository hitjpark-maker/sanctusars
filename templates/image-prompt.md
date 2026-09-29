# 생성 입력 작성

이제 전체 프롬프트를 매일 새로 쓰지 않는다. 고정 지시는 `brand/generation.json`에서 읽어 prepare가 조립한다.

1. 공식 복음을 확인하고 `templates/content.json`에 짧은 본문을 작성한다.
2. `templates/scenes.json`의 A/B/C 각각에 `scene`과 `scripture_relation`을 작성한다. 인물·행동·구도와 본문의 연결을 구체화한다. scripture_relation에는 강조한 말씀과 연결되는 눈가·입가·시선·자세·손 또는 공간의 관찰 가능한 단서를 적는다. 얼굴이 없는 장면에는 몸짓과 공간의 단서를 쓴다. 화풍과 질감 지시는 넣지 않는다. 원문에 있는 사실과 회화적 해석을 구분한다.
3. `python3 scripts/sanctusars.py prepare job.json content.json scenes.json`을 실행한다.
4. 출력된 준비 폴더의 실제 참조 이미지를 열어 본다. 각 request.json은 내장 imagegen의 입력 객체다. prompt, referenced_image_paths, transparent_background를 그대로 전달한다. 요약·추가·재해석하지 않는다.
5. 실제 이미지가 나온 후 해당 request 파일로 candidate에 등록한다.

A/B/C는 의미가 다른 장면이어야 한다. ‘다른 앵글’ 같은 빈 지시를 쓰지 않는다. 전체 화풍, 반복 질감, 실사 인물과 배경의 부조화, 기본 구성의 실패는 국소 편집으로 고치지 않는다. 확정 기준 안에서 장면·시점·표현 설계를 다시 판단하고 필요한 scenes 항목을 수정한 뒤 prepare로 해당 후보를 처음부터 새로 생성한다. 새 생성에는 준비된 확정 참조 두 장만 전달하며 실패 원본과 오류 확대 캡처는 넣지 않는다. 좋은 구도와 화풍 안의 국소 결함에만 refine을 쓴다. 자동 재작업은 후보별 새 생성 또는 국소 보정 한 차례 후 재검토하며, 남은 결함은 공개한다. 성공 후보와 이전 원본을 보존하고 사용자 승인 없이 확정 참조를 교체하지 않는다. 요청 파일이나 코드 테스트의 통과는 이미지 품질 통과를 뜻하지 않는다.
