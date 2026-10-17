# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0
- 참조 커밋 SHA: `b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0` (착수 시 실제 원격 main 확인)
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
