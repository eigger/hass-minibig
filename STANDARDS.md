# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/v1.1.2
- 참조 커밋 SHA: df9798509d9228247ec32efb313ec7b687b5b152
- Standards release: v1.1.2
- Resolved standards SHA: df9798509d9228247ec32efb313ec7b687b5b152
- 재검토일: 2026-10-20 (Asia/Seoul)
- profile: integration / ha
- 대상: `eigger/hass-minibig`, 실제 기본 브랜치 `main`, 시작 커밋 `790318e8998f170065b9dbfa909d58797f1b4950`와 이번 최신 기준 적용 작업 트리
- 조율 / 구현 / 독립 리뷰: root / implementation / review
- 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 지원 최소: HA `2025.8.0`, 통합 `0.3.0`, `blesession>=0.9.0` 유지

## 2026-10-20 최신 기준 재적용 (현재 판정)

공개 중앙 main `648dad941a118c80325f44c7a13cb5b5b9c1c788`을 `git ls-remote`로 확인하고 이전 기준 `0bfb572cbe49b92b3dbc559382c00bd0eb2cbd44` 이후 규칙·템플릿·도구 변경을 검토했습니다. 아래 절은 이전 채택의 역사적 근거이며 현재 작업 트리의 성공으로 재사용하지 않습니다.

양언어 README의 기존 설치 절에 중앙 렌더러로 My Home Assistant HACS 설치 배지를 추가하고, Default의 집계 배지를 HACS 공식 데이터의 HACS Downloads로 전환했습니다. HACS 선행 설치·사용자 다운로드/재시작, 선택 릴리스 asset 다운로드와 활성 설치 수의 차이·데이터 누락 의미를 양언어로 기록했으며 기존 본문·안전 안내·예제는 보존했습니다.

HA-02 제품 분류는 `blinds_curtains`를 주 분류, `plugs_switches`를 보조 분류로 선택했습니다. 실제 Window Opener의 창문 이동 위치·정지 용도와 PushMini/SwitchMini 스위치 제품이 근거이며 `minibig_ble/devices.py`의 프로필 및 `docs/usage.md`의 기기표·검증 DP 설명에 대응합니다. SwitchMini의 확인되지 않은 전원 DP 제한과 HubMini 미지원은 유지합니다. 엔티티 플랫폼에서 추정하지 않았으며 taxonomy 원본·선택 이유·검토자/날짜를 `.hass-standards.json.categories_review`에 기록했습니다. 이는 중앙 필수 정책이며 공식 HA 선택 필드·HACS 누락 경고와 구분합니다.

모든 중앙 workflow/action 및 `standards-ref`를 새 SHA에 고정했습니다. categories를 거부하는 published stable Hassfest 이미지 대신, 중앙의 선택 입력 `hassfest-core-ref: ec18d8b25d1ee39aa8b85a72a170e42bee33228c`로 categories 지원 변경을 포함한 공식 Core의 Dockerfile·entrypoint·전체 validator를 수정 없이 빌드하도록 설정했습니다. 이 선택은 검증 도구이며 HA 지원 최소·테스트 runtime 변경이나 검사 제외가 아닙니다. 조율자가 같은 검토 Core SHA의 깨끗한 source에서 공식 Dockerfile을 빌드한 뒤 원본 caller를 `/github/workspace`에 mount하여 전체 Hassfest를 실행했습니다. build와 validator 모두 종료0, Integrations1 / Invalid integrations0을 확인했습니다. 공개 중앙 문서의 과거 build 취소는 당시 기록이며 이번 실제 성공과 구분합니다. 추후 공식 이미지의 스키마 지원을 같은 대상에서 실제 검증한 뒤 입력 제거를 재검토합니다.

통합0.3.0·HA2025.8.0·blesession>=0.9.0 및 current2026.10.2/플러그인0.13.373/Python3.14, minimum2025.8.0/플러그인0.13.269/Python3.13을 유지합니다. 최종 diff·카테고리 의미·본문 보존 독립 리뷰와 최소/current 실제 HA107개 회귀·pip check, 공식 전체 Hassfest 독립 재실행을 통과했습니다. 미해결 필수 지적은 없으며 정확한 실행 환경·남은 원격 검증은 체크리스트의 최신 절에 기록했습니다. 승인 예외 없음. commit/push·새 원격 CI·중앙 현황 원격 반영은 수행하지 않았으며 실물·HA UI·배지 실시간 수치는 미검증입니다.

## 2026-10-20 HACS Default 재검토 (역사적 기록)

이 절은 HACS Default 반영 당시 판정이며, 아래 2026-10-19 및 2026-10-17 절과 함께 당시 검증·게시 대기 상태를 보존한 역사적 기록입니다. 2026-10-20 `git ls-remote https://github.com/eigger/hass-repo-standards.git refs/heads/main`으로 공개 중앙 main을 다시 확인한 결과 기존 참조 SHA와 동일합니다. 공개 SHA의 별도 checkout에서 AGENTS·README·채택 절차·체크리스트·관련 규칙·템플릿을 읽고 중앙 검사기를 실행했습니다.

기존 기준 적용은 [PR #24](https://github.com/eigger/hass-minibig/pull/24)로 main `3c7235280a57871c119def4056bcdffe78d4fa4a`에 반영되었습니다. 이 정확한 main SHA의 [Tests](https://github.com/eigger/hass-minibig/actions/runs/39410376782)와 [Validate](https://github.com/eigger/hass-minibig/actions/runs/39410376805)는 성공했습니다. 이번 재검토에서는 해당 반영 사실과 검증 근거를 현재화하고 HACS 기본 목록 등재를 문서·설정에 반영합니다. 이전 절의 “채택 PR·원격 CI 대기”는 당시 상태이며 현재 대기 항목이 아닙니다.

HACS 기본 목록의 [고정 커밋](https://github.com/hacs/default/blob/a75c02e2cb94db482c5aaddcc83d0dad00cc20a0/integration)에 `eigger/hass-minibig`가 포함됨을 2026-10-20 확인했습니다. `.hass-standards.json`을 `hacs: default`와 근거 URL·확인일로 갱신하고, 중앙 렌더러로 양언어 README의 Default 배지를 생성했습니다. README와 양언어 사용 안내의 설치 절차는 기본 목록에서 MiniBig 검색·다운로드로 정정했으며 그 밖의 본문을 보존했습니다.

중앙 통합 검사·Ruff·format·diff 검사는 이번 작업 트리에서 실행했습니다. 지원 최소 HA2025.8.0·통합0.3.0·blesession>=0.9.0, current HA2026.10.2/plugin0.13.373/Python3.14와 minimum HA2025.8.0/plugin0.13.269/Python3.13을 유지합니다. 정확한 검증 결과와 독립 리뷰는 체크리스트의 2026-10-20 절에 기록했습니다. 최종 HACS 문서 diff 독립 리뷰·중앙 통합/배지 검사 통과, 필수 미해결 지적 없이 로컬 적용을 완료했습니다. 실물 BLE 기기·새 proxy 보드·HA frontend UI는 이번 재검토에서 검증하지 않았으며 imagespec 미사용으로 DOC-08은 해당 없습니다.

중앙 현황은 조율자가 기존 checkout의 자기 리포 행에 이번 재검토를 로컬 반영했습니다. 해당 checkout에 기존 미게시 커밋이 있어 중앙 원격에 게시하지 않았습니다. 이번 문서 변경도 commit/push하지 않았으므로, 문서 작업 트리의 게시·새 SHA 원격 CI와 중앙 원격 현황 반영은 완료 근거와 구분합니다. 승인 예외는 없습니다.

## 2026-10-19 재검토 범위와 영향 (역사적 기록)

이전 기준 `b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0` 이후의 중앙 README 관리 영역·flat 배지·테스트 기반·공용 CI·DOC-07 기기별 문서 계약을 적용합니다. 중앙 템플릿과 렌더러를 사용하며 기존 영한 README 본문·설치 절차·사용 예제와 회귀 테스트를 보존합니다. 최신 원격 main은 `git ls-remote`로 확인했습니다. 중앙 로컬 checkout에만 있는 미게시 HACS 설치 안내 확장은 이번 기준에 포함하지 않습니다.

공용 workflow와 action, `standards-ref`는 위 전체 SHA로 고정합니다. Tests의 기존 주간 실행은 별도 Scheduled tests workflow로 보존합니다. 옵션 흐름 클래스 이름을 `MiniBigOptionsFlow`로 정리하여 중앙 검사기가 올바른 options 번역 영역을 확인하게 하며 설정 데이터·entry·unique ID·실제 옵션 동작은 유지합니다. `custom_components/__init__.py`와 공통 테스트 fixture, 플랫폼별 실제 HA 검증을 추가합니다.

로컬 적용·검증 후 사용자 후속 요청에 따라 브랜치에 커밋·푸시하고 채택 PR을 게시합니다. 태그·릴리스·수동 원격 workflow 실행은 수행하지 않습니다. 현재 트리의 로컬 검증과 이전 게시 커밋의 원격 CI를 구분하며, 새 원격 CI·중앙 게시 완료를 추정하지 않습니다. 정확한 실행 환경과 독립 리뷰 결과는 체크리스트에 기록합니다.

## 현재 예외와 검증 범위

승인 예외 및 독립 리뷰의 미해결 지적 없음. 최소/current HA×라이브러리 네 격리 환경에서 각107passed·skip0·pip check 통과, 독립 현재/최소 HA 재실행도 통과했습니다. 중앙 통합 검사·Ruff·actionlint 통과. 공개 중앙 원본 자체의 check_repository는 README 템플릿 header 오류로 실패했으며 현재 통합 검사 성공과 구분해 체크리스트에 기록했습니다.

중앙 현황은 로컬 자기 행만 적용·검증 결과로 갱신했으며 미게시입니다. 채택 PR의 새 SHA 원격 Tests/Validate와 중앙 게시 확인은 체크리스트의 TODO로 유지합니다. 실물 BLE 기기·새 proxy 보드·HA frontend UI는 이번 작업에서 검증하지 않습니다. imagespec requirement/import가 없어 DOC-08 payload 계약은 해당 없음입니다.

## 이전 적용 기록 (2026-10-17, 역사적 근거)

아래 기록은 이전 기준과 게시 커밋의 검증 이력이며 이번 작업 트리의 성공 근거로 재사용하지 않습니다.

- 표준: https://github.com/eigger/hass-repo-standards/tree/b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0
- 이전 참조 커밋 SHA: `b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0` (당시 착수 시 실제 원격 main 확인)
- 채택 작업일: 2026-10-17; 구현 main 반영·정확한 SHA 원격 검증·중앙 구현/검증 종료 보고 완료
- profile: integration / ha
- 실제 기본 브랜치: `main`; domain: `minibig`
- 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 조율: root / 구현: minibig_implementation·minibig_docs / 독립 리뷰: minibig_review
- 시작 대상: `c45775cf2179ae052fa0b1a47543ada91807f50e`
- 기존·적용 후 지원 최소: HA2025.8.0 (`hacs.json`과 기존 양 README 일치), 통합0.3.0·blesession>=0.9.0 유지
- current 실제 로컬검증: Python3.14.5 / HA2026.10.2 / pytest-homeassistant-custom-component0.13.373
- 최소 실제 로컬검증: Python3.13.14 / HA2025.8.0 / pytest-homeassistant-custom-component0.13.269
- 라이브러리 최소: blesession0.9.0. 실제 설치·pytest·pip check·원격CI는 점검표에 기록

## 범위와 영향

Core 대응 구현과 `tests/components/minibig/` 실제 HA 테스트, 공통CI·의존성 갱신, 영한 README·Usage·BLE 안내·진입 지침을 채택합니다. domain·entry 식별·지원 하한·통합 버전을 보존하고 이번 작업으로 태그/릴리스를 만들지 않습니다. 최신 테스트 실패는 호환 수정 대상으로 처리하며 지원 하한 상향으로 우회하지 않습니다. 기존 회귀 테스트와 상세 README·기술 문서·이미지를 보존합니다.

## 예외와 완료 근거

구현 네 환경 및 독립 양 HA 환경에서 각106passed skip0·pip check 통과, 기존79함수 보존. coordinator 생성자 예외 전에 외부 구독을 취득하지 않도록 순서를 보완하고 실제 HA 회귀를 추가한 뒤 최종 양 HA106개를 재검증했습니다. 현재 기록된 예외·미해결 로컬 필수 지적은 없습니다. 구현 main 반영·해당 SHA 원격 CI·중앙 구현/검증 종료 보고를 확인하여 적용 필수 항목은 PASS/N/A이며 현재 예외/TODO는 없습니다. 이 마감 문서의 후속 push·문서 SHA 원격 CI·중앙 최종 완료 상태 갱신은 조율자가 별도로 확인합니다. 시작 중앙 dbe3b96, 단계6e11e33 반영·각 중앙CI성공 확인. 실물 기기·새 proxy 보드·HA frontend UI는 이번 작업에서 미검증입니다. 원문 CLWM-B06 실물 기록은 과거 이력입니다.

## 실제 변경·독립 검증

실제 HA에서 확인한 cover 초기 poll값 누락을 live값 우선/오프라인 restore fallback으로 수정하고 양분기를 검증했습니다. setup 실패/취소·실제 플랫폼forward후실패의 BLE/광고listener/callback 정리를 보완했습니다. coordinator 생성자가 실패할 때 외부 구독을 취득하지 않도록 순서를 조정하고 실제 HA 회귀도 추가했습니다. HA bluetooth 직접사용 의존성, 서비스변경·GATT취소복구와 민감 주소/raw 로그 노출도 보완합니다. 의도된 로컬 raw 이벤트/진단 상태와 현재 unique ID는 보존합니다. 최종 테스트 함수105개/106cases, 기존79함수 누락0, 선택 enum미측정 프로필의 select 미노출도 확인했습니다.

최소 HA의 aiodns3.5와 호환되는 테스트전용 pycares4.11.0을 최소 requirements에 고정하고 runtime 요구사항·지원 하한은 유지합니다. current pycares5.2.0, blesession0.9.0(양mode), 전체 실제 버전/명령은 체크리스트가 원본입니다. 실제 구현 main `e70ee806dcbb8ebc561304253a8bbd373f9826b0`의 원격 Tests/Validate를 독립 확인했습니다.

최종 추가 경계 수정 뒤 독립 재검증: current106passed27.06s, minimum106passed26.07s(skip0)·양 pip check PASS. 구현 네 환경도 각106passed. 독립 로그 `/tmp/minibig-review-current-final2.log`, `/tmp/minibig-review-min-final2.log` (로컬 검증 이력; 게시 SHA 원격 증거는 별도 기록).

## 게시와 원격 검증

- 구현 main: [e70ee806dcbb8ebc561304253a8bbd373f9826b0](https://github.com/eigger/hass-minibig/commit/e70ee806dcbb8ebc561304253a8bbd373f9826b0)
- [Tests39042575895](https://github.com/eigger/hass-minibig/actions/runs/39042575895): lint2·HA×BLE4matrix 각106passed skip0 warning0·pip check PASS
- [Validate39042575896](https://github.com/eigger/hass-minibig/actions/runs/39042575896): brands포함 HACS·Hassfest PASS
- 원격 current Python3.14.8/HA2026.10.2/plugin0.13.373/BLE0.9.0/pycares5.2.0, 최소 Python3.13.16/HA2025.8.0/plugin0.13.269/BLE0.9.0/pycares4.11.0. BLE current/minimum 모두 정확한 설치값 확인
- 중앙 구현·검증 종료 보고: [b7b7d4cdf7df9b50bfd6405d3207873c1bb3f9e0](https://github.com/eigger/hass-repo-standards/commit/b7b7d4cdf7df9b50bfd6405d3207873c1bb3f9e0)

위 CI는 구현 커밋의 실제 결과입니다. 이 2문서 마감 커밋은 아직 미래의 SHA이므로 해당 성공을 추정하지 않습니다. 게시 후 독립 검증 담당이 자동 CI를 확인하고 중앙 최신 현황표에 최종 문서 커밋·CI와 완료 상태를 반영합니다. 실물·새 proxy 보드·HA frontend UI 미검증은 유지합니다.

## 2026-10-23 다운로드 배지 부분 갱신

- 배지·DOC-03/05와 Validate 형식 검사기만 중앙 [`b54ac48102d6e326c6929071fdc02ba8fade794e`](https://github.com/eigger/hass-repo-standards/tree/b54ac48102d6e326c6929071fdc02ba8fade794e)를 채택합니다. 이전 기준 SHA `648dad941a118c80325f44c7a13cb5b5b9c1c788`의 채택 이력·예외는 보존합니다. 모든 중앙 workflow/action pin과 standards-ref는 GOV-02의 단일 기준 SHA 계약에 맞춰 갱신합니다. 중앙 diff에서 공용 workflow/action 실행 파일은 이전 기준과 동일함을 확인했습니다.
- 대상 기본 브랜치 커밋: `b7053799d2a46fe06a2488d75476c208b2d3566c`. 주 에이전트 직접 구현·자체 리뷰(GOV-05의 배지/생성물 변경 범위), 검증은 [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md#2026-10-23-downloads-배지-부분-검증)에 기록합니다.
- Downloads는 모든 릴리스 첨부 asset 다운로드 합계입니다. 사용자 지시에 따라 ZIP 배포를 도입하지 않으며 현재 HACS 소스 파일 설치는 이 수치에 집계되지 않습니다. 통합 코드·의존성·지원 최소·기존 설치 안내는 변경하지 않습니다.

## 2026-10-23 ZIP 릴리스 배포

- 기준 중앙 SHA: `0c1592977591ecba077a4666d699840062711201` ([중앙 PR15](https://github.com/eigger/hass-repo-standards/pull/15) 스쿼시 머지). 이전 `b54ac48102d6e326c6929071fdc02ba8fade794e` 채택 이력·예외를 보존하며 HACS-04·CI-11의 ZIP 배포 계약을 추가합니다.
- 대상 시작 SHA: `1f5a99f4a5d94fc2e0272b9f5493f3511a586d0c`. hacs.json의 zip_release/filename과 중앙 release caller를 함께 적용합니다. archive 파일명은 `minibig.zip`, ZIP 루트는 해당 통합 파일입니다.
- 중앙 workflow/action pin과 standards-ref는 단일 SHA로 정합화합니다. release:published에서 기존 해당 릴리스에 ZIP만 첨부하며 소스 버전·태그·릴리스 발행은 자동 변경하지 않습니다. 기존 asset 덮어쓰기를 거부합니다.
- 기존 지원 최소 HA `2025.8.0`와 통합 버전 `0.3.1` 및 의존성·구현은 보존합니다. 기존 태그의 hacs.json은 소급 수정하지 않으므로 다음 릴리스부터 ZIP 설치로 전환됩니다.
- immutable-releases 설정은 enabled=false/enforced_by_owner=false로 확인했습니다. 업로드 지연·실패 및 기존 asset 복구는 중앙 [릴리스 계약](https://github.com/eigger/hass-repo-standards/blob/0c1592977591ecba077a4666d699840062711201/docs/releases.md#zip-릴리스-첨부)을 따릅니다. 실제 새 릴리스 발행·설치·기기 검증은 이번 작업에 포함하지 않습니다.

## 2026-10-25 중앙 검사기 갱신

- 검토한 중앙 main: `1863343638014adb8a4001afc8fddc1a27dc500f` (git ls-remote 확인). 이전 기본 기준 `0c1592977591ecba077a4666d699840062711201`의 채택 이력은 위 기록을 보존합니다.
- 모든 중앙 workflow/action pin과 reusable workflow의 standards-ref를 같은 검토 SHA로 맞춥니다. HACS-04는 actions/*의 full SHA 고정을 유지하면서 SHA 값 차이를 허용합니다.
- 통합 코드·런타임 의존성·지원 최소·배포 버전은 이번 변경 대상이 아닙니다. 기존 채택 범위를 전체 완료로 바꾸지 않으며 실제 검증 결과와 남은 항목은 ADOPTION_CHECKLIST.md의 같은 날짜 기록을 참조합니다.


### 2026-10-25 Standards 파일·표시 이름 분리

- 기존 Validate의 중앙 검사 job을 `standards.yml`로 옮기고 workflow/job 표시 이름을 `Standards`로 줄였습니다. Validate의 HACS/Hassfest, 검사 항목·통과 기준·실행 단계·조건·권한은 유지합니다.
- 위치 인식과 중앙 명명 안내를 맞춘 검토 소스: `ca740d88b32fa5dcbc94c41fce2908450c76ed50` ([중앙 PR #24](https://github.com/eigger/hass-repo-standards/pull/24), 현재 이 PR의 의존 변경). 이전 기준 `1863343638014adb8a4001afc8fddc1a27dc500f`의 검증 이력은 앞 기록으로 보존합니다. 모든 중앙 pin·standards-ref는 같은 새 검토 소스로 맞춥니다.

## 2026-10-25 중앙 immutable release 참조 전환

- 사용자 요청에 따라 현재 중앙 참조를 immutable `v1.0.0` / resolved SHA `44349ee5621eea5d80e5c427f7a2435d2c2491bb`로 전환했습니다. 중앙 workflow/action caller는 exact release tag를, `standards-ref`는 resolved full SHA를 사용합니다.
- 범위는 중앙 참조·기록 정합화뿐입니다. 기존 지원 최소, 통합 버전, manifest, 런타임 요구사항, 구현, 테스트와 CI의 caller-owned 설정은 보존했습니다.
- 과거 SHA·검증·예외 기록은 역사적 증거로 보존합니다. 이번 변경은 generated reference-only 범위이므로 GOV-05 자체 검토이며 PR CI/병합은 대기 상태입니다.
