# 공통 규칙 적용 체크리스트

MiniBig 첫 채택의 실제 점검 기록입니다. 미완료 항목은 TODO로 유지합니다. [사용법과 판정 기준](https://github.com/eigger/hass-repo-standards/blob/b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0/docs/checklist.md)을 읽고, 아래 규칙은 `STANDARDS.md`에 기록한 표준 커밋에서 확인합니다. 태그·릴리스 대신 검토한 전체 커밋 SHA를 기준으로 합니다.

## 검토 대상

| 항목 | 값 |
|---|---|
| 통합 리포 / 실제 기본 브랜치 | `eigger/hass-minibig` / `main` |
| domain / 구현 경로 | `minibig` / `custom_components/minibig/` |
| 검토 대상 통합 커밋 / 채택 PR | 시작 `c45775cf2179ae052fa0b1a47543ada91807f50e`에서 구현 최종 diff 로컬 검증. 게시 SHA·원격CI는 push 후 기록. 사용자 직접 push 지시, PR 없음 |
| 검토한 표준 전체 커밋 SHA | `b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0` |
| 검토일 / 조율 담당 | 2026-10-17 / root |
| 구현 서브 에이전트 / 독립 리뷰·검증 서브 에이전트 | minibig_implementation·minibig_docs / minibig_review |
| 중앙 현황표 반영일 / 기록 | 2026-10-17 시작 등록 [dbe3b96](https://github.com/eigger/hass-repo-standards/commit/dbe3b96a3b248fcf632e030a02a3c4f90a0e84a1) · [중앙 CI](https://github.com/eigger/hass-repo-standards/actions/runs/39041666477) 성공. 단계/종료는 검증 후 갱신 |
| 변경 전 지원 최소 HA / 근거 파일(hacs.json·manifest·README) | 2025.8.0 — hacs.json.homeassistant·기존 양 README 일치. manifest는 별도 최소 선언 없음 |
| 유지·변경할 지원 최소 / 변경 시 실제 비호환 근거·명시적 승인 | 2025.8.0 유지; 통합0.3.0·blesession>=0.9.0 보존 |
| current 테스트 HA / 호환 Python·플러그인 | HA2026.10.2 / Python3.14.5 / 플러그인0.13.373; 로컬 실제 설치 확인 |
| 최소 테스트 HA / 호환 Python·플러그인 | HA2025.8.0 / Python3.13.14 / 플러그인0.13.269; 로컬 실제 설치 확인 |
| profile / 테스트 경로 | integration / ha · tests/components/minibig/ |
| 이전 검토 기록 | 최초 채택 |
| 채택 판정 | 이관 진행 중 — 최종 로컬 구현·독립 검증 통과, 기본 브랜치 게시·해당 SHA 원격CI·중앙 종료 보고 대기 |

상태: `TODO` = 미확인·미충족, `PASS` = 근거로 확인, `EXCEPTION` = 적용 대상의 기록된 예외, `N/A` = 적용 조건에 해당 없음. 모든 항목은 미확인으로 시작합니다. `TODO`를 해당 없음으로 처리하지 않습니다. 묶은 규칙의 결과가 다르면 행을 나눕니다. 권장 항목은 별도로 표시했으며 미채택 이유를 기록합니다.

## 채택·구조·사용자 데이터

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| GOV-01, GOV-02 | `STANDARDS.md`에 표준 SHA·profile·실제 기본 브랜치·예외 기록, workflow/action은 검토 SHA로 고정 | PASS | [STANDARDS.md](STANDARDS.md) 기준 b1c80cf 전체 SHA·profile·main 기록. Tests/Validate/update_dependencies의 공통 호출 모두 해당 전체 SHA 고정. |
| GOV-03 | 새 표준 채택 변경의 영향·이관 방법과 명시적 채택 PR 확인. 규칙 자체를 변경하면 공통 CHANGELOG 기록 | PASS | 첫 명시적 채택이며 사용자 직접 push 지시로 검토한 diff를 반영. 기존 채택 기준 변경/중앙 규칙 변경 없음으로 후속 채택 PR·공통 CHANGELOG 변경 조건은 해당 없음. 영향은 STANDARDS·개발 문서에 기록. |
| GOV-04 | 중앙 표에 작업 시작·단계 변경·종료 상태, 담당·적용 내용·검증/리뷰 근거·남은 작업 갱신, 타 리포 기록 보존 | TODO | 시작 dbe3b96·단계 6e11e33 중앙 main 반영 및 각 CI 성공. 종료 보고·최종 기본 브랜치/원격 CI 근거 갱신 대기. 타 리포 행 보존. |
| GOV-05 | 구현과 독립 리뷰·검증을 별도 서브 에이전트에게 위임, 지적 수정·재검증 및 결과 취합 | PASS | 구현 minibig_implementation/minibig_docs, 독립 minibig_review. 독립 양 HA 최종 106passed skip0·pip check 통과. 초기 상태·restore·부분 플랫폼 rollback·구독 취소·로그/문서 지적 수정 후 재검증. |
| HA-01, HA-13 | `custom_components/<domain>/`와 domain 일치, 필요한 모듈·공개 API·생명주기는 Core 대응 구조 | PASS | custom_components/minibig/와 실제 HA ConfigEntry/플랫폼·coordinator·runtime_data·async lifecycle 구조. 실제 manager 테스트 test_init/test_platforms 통과. |
| HA-02 | manifest 필드·정렬·동작 선언 확인, 공식 품질 등급 자가 표기 없음 | PASS | manifest domain minibig/name/config_flow/iot_class/local_polling·version0.3.0 보존, 실제 사용하는 HA bluetooth dependency로 정정. 공식 quality scale 선언 없음. 원격 Hassfest는 별도 대기. |
| HA-03 (권장) | 공통 상수·설정·갱신·플랫폼 역할 및 프로토콜 경계에 맞게 모듈 구성 | PASS | const/types/config_flow/coordinator/services/session_report와 minibig_ble parser/writer/devices/client 경계 유지. |
| HA-04, HA-08 | UI 설정·중복·안정적 식별 및 기능별 options/reauth/reconfigure, entity 의미·registry 영향 확인 | PASS | test_config_flow의 Bluetooth·사용자 추가/중복/HubMini거부/미발견/옵션 reload, test_platforms의 cover·switch·number 액션과 registry/state 확인. reauth/reconfigure는 기존 인증/재구성 기능 없음. |
| HA-01, HA-04, HA-08, REL-01, REL-03 | domain·unique ID·entry schema·상태/통계 계약 변경 시 migration 테스트와 사용자 조치 안내 | PASS | domain·unique ID·entry version/data계약 유지. test_init의 저장ID복원/광고identity자가복구/기존 stale entity정리·현재 ID유지 및 test_config_flow 옵션reload 확인. 새 entry schema migration 없음; 기존 stale정리 회귀는 실제 registry로 검증. |
| HA-05, HA-06 | setup 실패 구분, unload/reload·부분 실패의 task/listener/연결 정리, async·timeout·취소 처리 | PASS | test_init에서 subscribe 중 setup취소·refresh후예외·실제 플랫폼forward후실패 rollback·unload의 링크/worker/광고listener/보고 callback 정리 확인. BLE close·작업취소·서비스변경 회귀 보존. |
| HA-07 | 중복 polling·property I/O 방지, push 보존, unavailable/unknown·실패 후 복구 | PASS | 초기 실제 poll값을 cover에 적용하고 live우선/오프라인 restorefallback 양분기 test_platforms 확인. movement push·이동중pollskip·범위밖 비치명poll·실패진단·재연결 회귀 포함; property I/O 없음. |
| HA-11, HA-12 | 번역·action/schema 일치, 로그/diagnostics/fixture 비식별화와 제공 시 redaction 테스트 | PASS | strings/en/ko 및 services.yaml/schema 대응, test_services 검증오류·실액션·로그 주소/rawdata 비노출 회귀. 기존 로컬 raw_response 이벤트·진단 속성은 계약 보존; 공개 전 비식별 안내. diagnostics 다운로드 기능은 없음. |

## 실제 HA 테스트·호환성·의존성

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| TEST-08 | `tests/components/<domain>/`에 구현과 대응하는 테스트·domain fixture 배치, discovery·CI 경로 일치 | PASS | 기존 회귀를 tests/components/minibig/로 이동하고 domain conftest/fake_transport 배치; CI pytest 경로 일치. |
| TEST-02, TEST-03, DEP-07 | 실제 HA·호환 플러그인과 `hass`/`enable_custom_integrations` fixture 사용, HA core stub/복사본/`--no-deps`로 대체하지 않음 | PASS | 실제 hass·enable_custom_integrations·MockConfigEntry/helper·habluetooth manager 사용. 외부 BLE/GATT transport만 대체; HA stub·fake manager/platform·--no-deps·import skip 없음. |
| TEST-09 | 실제 loader·config entry manager로 setup/플랫폼 로딩, HA 상태·registry·service/action으로 결과 검증 | PASS | test_init의 실제 entry manager setup/플랫폼/registry/state/unload, test_config_flow 실제 flow manager, test_services/test_platforms 실제 HA actions와 상태 검사. select는 기존 모든 프로필의 미확인 enum mapping으로 노출 안 됨을 검사. |
| TEST-01, TEST-06, TEST-07 | 구현 기능별 성공·실패·중복·migration·unload·복구 회귀 검증, 외부 통신 경계만 mock, skip 사유 | PASS | 기존 79개 test함수 누락0, 최종105함수/106cases. parser·writer·client·coordinator·sessionreports 회귀와 신규 actualHA lifecycle/flows/actions/restore/cleanup 통과. 두 HA 모두 106passed skip0. 새 schema migration/인증 기능 해당 없음; stale entity cleanup 회귀 유지. |
| TEST-04, HACS-01 | 변경 전 지원 최소·current·각 Python/플러그인 분리, 선언한 정확한 최소 검증, 상향 시 비호환 근거·명시적 승인 확인 | PASS | 기존 지원 최소 HA2025.8.0 보존. 최소 Python3.13.14/HA2025.8/.269와 current Python3.14.5/HA2026.10.2/.373 별도 환경 실제 설치·106passed·pip check 확인. 최소를 올리거나 최소 환경 제거하지 않음. |
| TEST-05, HA-10, DEP-02, DEP-05 | imagespec·blesession 등 최소/현재 라이브러리 별도 환경, 실제 HA 테스트·정확한 설치값·API 경계 검증 | PASS | HA별 current/minimum blesession 별도 네 환경 각106passed·pip check. 양 mode 실제 blesession0.9.0이며 minimum은 manifest >=0.9.0 정확 하한 assertion. 서비스맵 변경·GATT절단/취소/재연결 회귀 유지. |
| DEP-01, DEP-06 | Python runtime은 manifest requirements, HA domain은 dependencies/after_dependencies, 테스트·린트 requirements는 별도 | PASS | manifest Python requirements blesession>=0.9.0 유지, HA dependency bluetooth(실제 사용) 선언; requirements_test/current/minimum·requirements_lint 별도. |
| DEP-07, CI-06 | 실제 사용하는 HA 구성요소의 requirements·필수 재귀 의존성·선택 로딩 경로 설치, resolver·`pip check` 통과 | PASS | 공통 actions/python-environment/install.py로 manifest+bluetooth 및 실제 sensor/binary_sensor/button/switch/cover/select/number 재귀requirements를 한 resolver로 설치. 네 구현 환경·양 독립 환경 pip check 및 실제 HA tests 통과. |
| DEP-02, DEP-03, DEP-08 | 의존성 추가/변경의 버전·extras·marker·선언 위치·지원 플랫폼·라이선스 검토, 실제 HA 테스트와 문서 갱신 | PASS | 새 runtime Python 패키지 추가/연산자변경 없음. HA bluetooth domain 정정은 API 직접사용과 실제 로딩 근거. current HA/plugin exact pins, 최소 테스트전용 pycares4.11 호환성·격리/제외 및 개발명령 문서화. BLE0.9.0/PyPI metadata 독립 확인. |

독립 리뷰는 변경 전후 지원 최소와 current를 비교하고, 봇 PR이 과거 최소 requirements·constraints까지 갱신하거나 expected-ha-version·Python을 누락하지 않았는지 확인합니다. 최신 테스트 실패는 호환 수정 대상으로 처리합니다.

환경마다 아래 행을 복사합니다. 최소 HA와 최소 라이브러리 검증을 혼동하지 않고, marker가 활성인 환경에서 대상 패키지 설치값을 확인합니다. 실행하지 않은 조합은 `TODO` 또는 근거가 있는 `EXCEPTION`으로 남깁니다.

| 검증 축 / 상태 | 통합 커밋 | Python / HA / 플러그인 실제 버전 | 대상 패키지 실제 버전·extras·marker | 명령·테스트 결과·pip check / CI run·job | skip·제외·미검증 범위 |
|---|---|---|---|---|---|
| 구현 current HA × current/minimum BLE / PASS | 최종 로컬 diff (게시SHA 대기) | Python3.14.5 / HA2026.10.2 / plugin0.13.373 | blesession0.9.0 양mode, extras/marker없음; pycares5.2.0 | 별도2venv sharedinstaller→pytest tests/components/minibig/ -q→pip check 각106passed skip0 | 실물/UI미검증 |
| 구현 minimum HA × current/minimum BLE / PASS | 같은 최종 로컬 diff | Python3.13.14 / HA2025.8.0 / plugin0.13.269 | blesession0.9.0 양mode, pycares4.11.0 | 별도2venv 동일명령 각106passed skip0·pip check | 실물/UI미검증 |
| 독립 current HA / PASS | 같은 최종 로컬 diff | Python3.14.5 / HA2026.10.2 / plugin0.13.373 | blesession0.9.0 / pycares5.2.0 | 독립env manifest/HA재귀설치→pytest tests/components/minibig/ -v 106passed skip0·pip check | 실물/UI미검증 |
| 독립 정확한 최소 HA / PASS | 같은 최종 로컬 diff | Python3.13.14 / HA2025.8.0 / plugin0.13.269 | blesession0.9.0 / pycares4.11.0 | 독립env pytest tests/components/minibig/ -v 106passed skip0·pip check | macOS asyncinotify 경고1(플랫폼차이); Linux CI대기 |
| 게시 SHA 원격 CI / TODO | 미게시 | 실제runner버전 확인대기 | 네 matrix 설치값확인대기 | Tests·HACS/Hassfest 대기 | 실제원격결과미확인 |

## HACS·CI·의존성 업데이트

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| HACS-01, HACS-02 | 루트 README/LICENSE/hacs.json, 검증한 최소 HA, 실제 배포 구조와 필요한 옵션 일치 | PASS | 루트 README/LICENSE/hacs.json, custom_components/minibig 배포. hacs.homeassistant2025.8.0 유지·실제 최소106tests통과, 불필요 zip/content 옵션 추가 없음. |
| HACS-03, HACS-05 | Default 여부는 목록 근거로 확인, [로컬 brand/icon.png 또는 원격 brands 근거](https://github.com/eigger/hass-repo-standards/blob/b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0/docs/hacs.md)와 HACS/Hassfest 실제 실행, ignore는 이유·해제 조건 기록 | TODO | HACS Custom 표기. 기존 brand/icon 실제PNG256×256 RGB, 기존512×512를 icon@2x로 보존; logo444×128 RGBA 유지. 기존출처 e205ba1·MIT·권리한계 development 기록. 브랜드 포함 원격 HACS/Hassfest 정확 게시SHA 검사 대기; ignore 없음. |
| HACS-06 (권장) | description·topics·issue 경로·brands 및 사용하는 HACS 필드 지원 확인 | PASS | 실제 원격 Issues/Discussions·MIT·main·정식 v0.3.0 확인. 로컬 brand 실형식 확인; description/topics 설정은 이번 범위에서 변경하지 않음. 임의 HACS 필드 없음. |
| CI-01, CI-02 | Validate/Python Tests 공통화, 확장 job 유지, PR·실제 기본 브랜치 push·dispatch 및 필요한 schedule | PASS | Tests·Validate·Update dependencies 중앙재사용으로 통합. Tests/Validate는 mainpush·PR·dispatch·schedule, updater는 weekly/dispatch. 기존 별도 UI/build job 없음. |
| CI-03, CI-05, CI-08 | 최소 권한·checkout 자격증명 비보존·timeout·concurrency, full SHA·갱신 관리, 비신뢰 입력·secrets 경계 | PASS | caller contents:read, updater job만 contents/PRwrite. 중앙 pin b1c80cf·actions fullSHA·checkout credentials비보존·timeout/concurrency·bot비취소. Dependabot 액션갱신, untrusted PR metadata shell직삽입/secrets inherit 없음. |
| CI-04, CI-07, CI-12 | 실패를 숨기지 않는 실제 `ha` 필수 테스트, 버전별 환경·cache·Ruff 설정과 required checks 이름 확인 | PASS | ha 필수·최소/current HA×BLE 네 matrix, lint별도; 실패은폐/skip없음, cache와 requirements/manifest 포함. 원격 branch protection404/rulesets[]라 기존 required check 없음·설정변경없음. 원격 실행결과는 아래 TODO. |
| DEP-03, DEP-04, CI-09 | updater의 선택 package·연산자/extras/marker 보존, 안정 버전·major 정책, 실제 기본 브랜치·단일 bot branch·PR만 제안 | PASS | update_dependencies.yml blesession만 선택·기준SHA핀 중앙bot 사용. 안정 PyPI/연산자 보존·기본브랜치 API·단일 bot branch·PR제안만. 독립 dry-run unchanged blesession0.9.0; 최소 requirements/constraints Dependabot 제외, current HA/plugin group. |
| CI-09, CI-10, DEP-08 | 변경 tree의 새 하한·실제 HA 검증 후 PR 동기화, 실패 시 중단·변경 없음 시 기존 PR 정리, 후속 required checks 충족 방식 확인 | PASS | 중앙 updater의 변경 tree 새 정확하한 설치·실제 ha 테스트+lint 후 PR 동기화/실패중단 계약 사용. dry-run 변경없음 독립확인; writable dispatch/가짜update PR 실행하지 않음. GITHUB_TOKEN PR이 자동CI보장하지 않음을 development에 명시. |

## README·Bluetooth·유지보수

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| DOC-01, DOC-02, DOC-06 | 영어 README.md·한국어 README.ko.md·상호 링크·기존 내용 보존, 간결한 제목/소개/핵심지원/최소요구/빠른설치·설정/짧은예제/중요제한/문서목록, 상세옵션·긴YAML·참조·개발/실HA테스트·의존성/검증범위를 docs·examples 등으로 보존·분리하고 유효한 링크 제공, 실제 활성 Issues·Discussions 또는 대체 지원 경로·실제 LICENSE 링크 | PASS | README.md 영문·README.ko.md 한글 상호링크/간결한시작·설치/예제/물리안전·문서/지원/MIT. README.en 기존진입호환. 기존상세영한본문·protocol/architecture/이미지보존; 실제모델분류/DP한계/schema 정정. development 실제명령·버전/의존성절차. 로컬링크 누락0·독립문서리뷰 통과. |
| DOC-03, DOC-04, DOC-05 | 제목 아래 관리 블록, flat-square·순서·실제 조건별 배지, CI 실제 기본 브랜치, 필수 동적 Usage·Analytics 참여 설치 의미·미집계/조회 실패와 0 설치 구분·이전 안내 보존 | PASS | 관리블록 flat-square HACS/실제정식Release/최소HA/Tests/Validate/License/Usage 순서. branch main·$.minibig.total 사전조회없이생성. Analytics opt-in·미집계≠0 고지, sync_badges --check PASS. |
| HA-09, HA-10 | BLE 사용 시 HA Bluetooth API·라이브러리 공개 경계, 지원한 proxy 경로·재연결·취소·서비스 변경 검증 | PASS | HA bluetooth 공개 발견/API→실제 BLE boundary·blesession 공개경계. 기존 client 서비스변경·취소·slot회복 및 실제HA절단/재연결/cleanup 검증. 실물proxy는 별도 미검증. |
| DOC-07 | blesession/proxy 통합 README의 핵심조건·상세문서 링크, 공통 Bluetooth 설정·추천기기·active 스캔/GATT 차이, 통합별 troubleshooting 또는 공통 링크+모델고유조건·실제진단·민감정보 제거 제보 안내 | PASS | 영한README 공통Bluetooth/추천기기링크, troubleshooting영한별도. active scan과 active GATT·모델차이/전원·초기앱캘리브레이션·경쟁앱/슬롯/keepconnected·보고센서/raw이벤트 경로 명시. ESL전용옵션 복사 없음. |
| DOC-07, HA-12 | 기기별 깨우기·인증·타 앱 연결·전송 제약, 실제 검증 경로와 미검증 범위, 공개 문제 로그 비식별화 | PASS | 트러블슈팅 모델별깨우기/인증추정금지·공식앱초기설정·DP제약·raw/초기화물리안전·공개전주소/프록시/packet/ID/상태비식별 안내. 과거CLWM-B06관측과 새실물/UI/보드미검증 구별. |
| HACS-04, REL-01, REL-02, REL-03, CI-11 | 통합 릴리스 시 같은 검증 commit/tag·manifest 버전·산출물·권한, 사용자 영향·지원 변경·제한 안내 | N/A | 이번 작업은 공통 규칙 채택이며 새 tag/Release/asset 생성 안 함. 통합0.3.0 유지; 기존실제정식 v0.3.0 배지만 연결. 향후 릴리스는 검증commit/tag/manifest 일치·변경/지원영향 안내 후 별도 수행. |
| REL-04 | 이전/중단 시 README 상단 경로·유지보수 상태·재등록 여부, 자동 이전으로 오인하지 않는 안내 | N/A | 리포 이전·통합·중단 작업 없음. domain/기기 재등록 불필요; 기존README.en 진입호환 보존. |
| REL-05 (권장) | 의존성/HA API 변경과 기능 변경 분리, 표준 변경은 명시적 채택 PR로 반영 | PASS | 공통규칙채택과 필요한 실제HA lifecycle·호환성결함수정 범위. 기능/릴리스확장없음; 추가 채택기준변경은 명시검토. 지원정책 보존. |

## 예외와 남은 작업

예외 원본은 `STANDARDS.md`입니다. 아래에 해당 위치를 연결하고, 예외가 실제 없음을 확인한 뒤에만 `없음`으로 바꿉니다.

| 규칙 ID | 예외 위치 / 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 (현재 로컬검토) | 기록된 예외 없음; 원격/중앙종료 필수 TODO는 예외로 대체하지 않음 | root | 최종원격검증후재확인 |

| 규칙 ID / TODO | 남은 작업 / issue·PR | 담당자 | 완료 근거 |
|---|---|---|---|
| GOV-04, HACS-05, 원격CI | 기본브랜치push·게시SHA Tests/Validate·중앙종료·체크리스트마감 대기 | root·minibig_docs·minibig_review | 아직미완료 |

최종 검토 시 적용 대상 필수 `TODO`와 `EXCEPTION`, 이유가 있는 `N/A`, 권장 미채택을 구분해 적습니다. CI 성공만으로 실물 기기 검증을 주장하지 않습니다. 실물 검증을 수행했다면 모델·펌웨어·어댑터/proxy·연결 경로와 결과를 별도로 기록합니다.

중앙 보고는 [적용 현황표](https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md)의 자기 리포 행에 반영합니다. 리뷰 지적·수정·재검증 결과와 중앙 갱신 실패 사유가 있으면 남은 작업에도 기록합니다.

## 검증 기록 세부

2026-10-17 최종 구현 freeze 후 구현 담당 네 격리 환경과 독립 리뷰 담당 두 격리 환경에서 동일 tree의 actual HA 106cases 모두 통과했습니다. 기존 79함수 모두 보존, 최종105함수(한 파라미터 추가로106cases), skip0입니다. 신규 coverage는 실제 setup/flow/options·registry/state/actions·저장identity·stale정리·광고자가복구·live/restore양분기·실제partialforwardrollback·subscribe취소·coordinator생성자실패전구독미취득·오류진단·number DPoverride입니다. select는 기존 프로필 모두 enum값 미측정으로 노출하지 않는 조건을 확인했으며 미구현 선택값을 만들어 지원으로 주장하지 않습니다.

명령: docs/development.md의 INPUT_DOMAIN=minibig·ha profile·각 requirements·expected HA·ha-components로 shared installer(bootstrap pip/packaging, RUNNER_TEMP 별도), 구현 환경에서 `python -m pytest tests/components/minibig/ -q`, 독립 환경에서 `python -m pytest tests/components/minibig/ -v`, 양쪽 `python -m pip check`. 최소/current 라이브러리는 별도 환경으로 설치했습니다. Ruff check/format(49files), actionlint(shellcheck/pyflakes별도비활성), diffcheck PASS. 독립 updater PyPI dry-run은 blesession0.9.0 변경없음. `sync_badges.py --check`, 로컬파일링크 누락0, 중앙 check_repository 26문서7workflow PASS. 설치/린트와 실제HA성공은 구별하며 아직 게시하지 않은 SHA의 원격결과를 주장하지 않습니다.

브랜드는 초기 e205ba10b4616c28db8aa9f538b928d6b1ef5697의512 PNG icon을 icon@2x로 보존하고256 icon을 추가했습니다. logo444×128 RGBA는 보존. 출처·기존MIT와 권리/표시 한계는 development에 기록했습니다. 실물·새프록시보드·HA frontend UI는 미검증이며 과거README CLWM-B06관측과 분리합니다.

최종 추가 경계 수정 뒤 독립 재검증: current106passed27.06s, minimum106passed26.07s(skip0)·양 pip check PASS. 구현 네 환경도 각106passed. 독립 로그 `/tmp/minibig-review-current-final2.log`, `/tmp/minibig-review-min-final2.log` (로컬 검증 이력; 게시 SHA 원격 증거는 별도 기록).
