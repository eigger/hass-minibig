# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/0bfb572cbe49b92b3dbc559382c00bd0eb2cbd44
- 참조 커밋 SHA: `0bfb572cbe49b92b3dbc559382c00bd0eb2cbd44`
- 재검토일: 2026-10-19 (Asia/Seoul)
- profile: integration / ha
- 대상: `eigger/hass-minibig`, 실제 기본 브랜치 `main`, 시작 커밋 `04a425c1b2071ceb705b06fdf1d956daedcdaaf4`의 후속 작업 트리
- 조율 / 구현 / 독립 리뷰: root / implementation / review
- 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 지원 최소: HA `2025.8.0`, 통합 `0.3.0`, `blesession>=0.9.0` 유지

## 2026-10-19 재검토 범위와 영향

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
