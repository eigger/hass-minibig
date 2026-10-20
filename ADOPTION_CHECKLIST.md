# 공통 규칙 적용 체크리스트

## 2026-10-20 후속 재검토

이 절이 현재 판정입니다. 아래 2026-10-19·2026-10-17 기록은 당시의 검증·게시 상태를 보존합니다. 이전 절의 PR·원격 CI 대기 항목은 [PR #24](https://github.com/eigger/hass-minibig/pull/24)의 main 반영과 아래 정확한 SHA의 성공으로 해소되었습니다.

| 항목 | 현재 확인 내용 |
|---|---|
| 대상 / 검토 커밋 | `eigger/hass-minibig` / 실제 기본 브랜치 `main` / `3c7235280a57871c119def4056bcdffe78d4fa4a`와 이번 문서 변경 작업 트리 |
| 검토한 표준 | 공개 중앙 main `0bfb572cbe49b92b3dbc559382c00bd0eb2cbd44` — 2026-10-20 `git ls-remote ... refs/heads/main` 재확인, 기존 적용 SHA와 동일 |
| 담당 | 조율 root / 구현 implementation / 독립 리뷰 review |
| 변경 범위 | 재검토 기록·완료된 PR/CI 상태 현재화, HACS Default 설정·양언어 배지·README/사용 안내 설치 절차 수정. 구현·테스트·CI·requirements 변경 없음 |
| 지원 정책 | HA2025.8.0·통합0.3.0·blesession>=0.9.0 유지. current Python3.14/HA2026.10.2/plugin0.13.373, minimum Python3.13/HA2025.8.0/plugin0.13.269 유지 |
| 정확한 main SHA 원격 CI | [Tests39410376782](https://github.com/eigger/hass-minibig/actions/runs/39410376782) / [Validate39410376805](https://github.com/eigger/hass-minibig/actions/runs/39410376805) 성공. 이번 미게시 문서 작업 트리의 원격 실행 결과와 구분 |
| 중앙 현황 | 조율자가 기존 중앙 checkout의 MiniBig 행만 로컬 갱신. 기존 미게시 중앙 커밋을 보존하여 원격 미게시 |
| 판정 | 기존 기준의 main 반영 및 정확한 SHA 원격 CI 성공 확인. 이번 HACS 수정·재검토·독립 리뷰는 로컬 완료. 대상 문서 변경과 중앙 현황은 원격 미게시 |

| 규칙 | 상태 | 이번 확인과 근거 |
|---|---|---|
| GOV-01, GOV-02 | PASS | 공개 중앙 기준과 현재 참조 SHA 일치. 중앙 검사기의 README·테스트 기반·공통 caller·전체 SHA 검사 종료0 |
| GOV-03 | PASS | 기존 명시적 채택 PR #24 main 반영 확인. 중앙 기준·구현 변경이 없어 새 기능/지원 정책 이관 없음 |
| GOV-04 | TODO | 시작·검증 단계의 중앙 자기 행 로컬 갱신 완료. 기존 중앙 checkout의 미게시 커밋을 보존하며 원격 보고는 미반영 |
| GOV-05 | PASS | 구현 implementation과 별도 review 담당 분리. 정확한 main SHA 원격 로그·HACS 등재 근거·최종 diff 독립 검토 완료. 중앙 통합/배지 검사 재실행 종료0, 미해결 필수 지적 없음 |
| DOC-01~07, TEST·CI 계약 | PASS | 기존 관리 영역·공용 CI·테스트 기반을 공개 SHA 중앙 검사기로 이번 작업 트리에서 검사. 이번 변경의 HACS 설치 안내 외 본문·구현·기존 테스트 그대로 보존 |
| HACS/Hassfest, 실제 HA 원격 검증 | PASS | 정확한 검토 main SHA의 Tests/Validate 성공. review 담당이 설치값·107passed/skip0·pip check·HACS brands·Hassfest·중앙 템플릿 성공 로그 독립 확인 |
| DEP·HA 지원 하한 | PASS | manifest/hacs/current·minimum requirements 및 양 HA×라이브러리 matrix 확인. 하한·연산자·버전 조합 변경 없음 |
| DOC-08 | N/A | imagespec requirement/import 및 payload 렌더링 기능 없음 |
| 실물/UI | 미검증 | 실물 MiniBig·새 proxy 보드·HA frontend UI 검증 수행 안 함 |

### 이번 실행 근거와 남은 작업

- 공개 SHA의 별도 checkout `/tmp/minibig-standards-20261020`에서 중앙 지침·채택/체크리스트·관련 규칙·템플릿 확인. 기존 중앙 작업 트리의 미게시 변경은 검사 기준으로 사용하지 않았습니다.
- `python3 /tmp/minibig-standards-20261020/scripts/check_integration.py --help`로 실제 CLI 확인 후 `python3 /tmp/minibig-standards-20261020/scripts/check_integration.py . --check`: 종료0.
- `ruff check .`: 통과. `ruff format --check .`: 56 files already formatted. `git diff --check`: 통과. 이번 문서 변경으로 실제 HA 테스트를 새로 실행했다고 기록하지 않으며, 위 정확한 main SHA 원격 실행 근거를 사용합니다.
- 독립 원격 로그 검토: 정확한 main SHA의 네 matrix 모두 **107 passed**, pytest skip0·`pip check` 통과. current Python3.14.8 / HA2026.10.2 / plugin0.13.373 / pycares5.2.1, minimum Python3.13.16 / HA2025.8.0 / plugin0.13.269 / pycares4.11.0. 네 환경 모두 실제 blesession0.9.0. 로그 `/tmp/minibig-review-tests-ci.log`, `/tmp/minibig-review-validate-ci.log`. 원격 Validate는 HACS brands·Hassfest·중앙 템플릿 검사 성공이며 이번 변경 후 원격 실행을 뜻하지 않습니다.
- HACS-03/DOC-03: [hacs/default 고정 목록](https://github.com/hacs/default/blob/a75c02e2cb94db482c5aaddcc83d0dad00cc20a0/integration)의 `eigger/hass-minibig` 등재를 2026-10-20 확인. `.hass-standards.json`의 `hacs: default`·근거/확인일과 중앙 렌더러의 양언어 Default 배지 반영. README/사용 안내의 사용자 지정 저장소 등록 필수 절차를 기본 목록 MiniBig 검색·다운로드로 정정했습니다. 한국어 사용 안내의 README 링크도 한국어판으로 맞추고 나머지 본문을 보존했습니다.
- 중앙 원본 자체 검사: root와 review가 공개 SHA의 clone에서 `python3 scripts/check_repository.py` 실행, **Checked 37 documents, 7 workflows, JSON and caller input contracts**, 종료0. 2026-10-19의 중앙 자체 검사 실패는 당시 환경의 역사적 기록으로 분리합니다.
- 최종 HACS 문서 diff 독립 리뷰 통과, 필수 미해결 지적 없음. review 담당의 `check_integration.py . --check`와 `sync_badges.py . --check` 각각 종료0, root도 중앙 통합 검사·diff 검사 재실행 종료0. 이번 문서 작업 트리 commit/push·그 새 SHA의 원격 CI는 미실행이며 중앙 현황 원격 반영도 남아 있습니다. 승인 예외 없음.

## 2026-10-19 후속 재검토 (역사적 기록)

이 절은 2026-10-19 당시 판정입니다. 아래 2026-10-17 기록과 함께 당시 게시 커밋·작업 트리의 이력으로 보존하며, 현재 판정은 맨 위 2026-10-20 절에서 확인합니다.

| 항목 | 현재 확인 내용 |
|---|---|
| 대상 / 시작 커밋 | `eigger/hass-minibig` / `main` / `04a425c1b2071ceb705b06fdf1d956daedcdaaf4` 후속 채택 PR 작업 트리 |
| 검토한 표준 | `0bfb572cbe49b92b3dbc559382c00bd0eb2cbd44` — 2026-10-19 `git ls-remote ... refs/heads/main` 확인 |
| 이전 기준 | `b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0` |
| 담당 | 조율 root / 구현 implementation / 독립 리뷰 review |
| 적용 profile | integration / ha, `tests/components/minibig/` |
| 지원 정책 | `hacs.json` HA2025.8.0·manifest 통합0.3.0·blesession>=0.9.0 유지, requirements 변경 없음 |
| 원격 메타데이터 | GitHub API: 기본 main, Issues/Discussions 활성, MIT, 최신 Release v0.3.0, rulesets=[], branch protection404 |
| 중앙 현황 | 중앙 로컬 `docs/adoption-status.md`의 MiniBig 행만 로컬 적용·검증 완료/게시 대기로 갱신. commit/push 미수행으로 원격 현황 미반영 |
| 판정 | 로컬 적용·독립 리뷰·최소/current HA×라이브러리 네 환경 검증 완료. 사용자 후속 요청으로 채택 PR 게시 단계이며 원격 Tests/Validate 결과 대기이므로 전체 채택은 진행 중 |

| 규칙 | 상태 | 이번 변경과 근거 |
|---|---|---|
| GOV-01, GOV-02 | PASS | STANDARDS 현재 참조 필드·모든 workflow/action·standards-ref를 같은 공개 전체 SHA로 고정. 이전 검증은 역사적 절로 분리 |
| GOV-03, GOV-04 | TODO | 사용자 요청에 따른 로컬 재검토·영향 기록과 중앙 로컬 자기 행 갱신 완료. 사용자 후속 요청으로 브랜치 커밋·푸시·채택 PR 게시를 진행하며 정확한 새 SHA 원격 CI·중앙 원격 보고는 후속 확인 |
| GOV-05 | PASS | 구현/독립 리뷰 담당 분리. 독립 DOC-07 지적을 보완한 뒤 영한 문서·실제 코드 의미·중앙 검사·현재 HA 전체 테스트 재검증 통과. 최소 HA 실행은 별도 항목에 기록 |
| DOC-01~06 | PASS | 중앙 렌더러의 영한 header/support/related-projects/license, flat 배지 적용. 기존 Devices~Documentation 본문은 공통 안내 URL 교체 외 동일; 독립 의미 리뷰 별도 |
| DOC-07 | PASS | blesession 영한 사용자 원본 링크·고정 H2·증상 표·기존 기기 안내 보존. 독립 리뷰의 세션 오류/완료 확인/연결 경로 설명을 보완한 뒤 양언어와 실제 client/session_report 의미 재검증 통과 |
| TEST-01~09, HA-11 | PASS | 정확한 중앙 루트 conftest·빈 init·domain 관리 블록/fixture alias·플랫폼별 실제 HA 테스트 적용. 기존 테스트 함수105개 AST 보존, select 미지원 enum 회귀 1개 추가. 최소/current HA×라이브러리 네 환경 각107passed·skip0·pip check 및 독립 양 HA 재실행 통과 |
| CI-01~08, CI-12 | PASS | 공통 caller·standards 검사 job·SHA/standards-ref 적용. 기존 Tests 주간 실행은 scheduled_tests.yml에서 같은 current/minimum HA×라이브러리 matrix로 보존. actionlint 정적 검증 통과 |
| DEP, HA 지원 하한 | PASS | manifest/hacs/requirements 원본 유지. 최소 HA와 라이브러리 정확한 하한 검증을 분리하며 하한 상향 없음 |
| DOC-08 | N/A | imagespec requirement/import 및 payload 렌더링 기능 없음 |
| HACS/Hassfest, 원격 CI | TODO | 이번 채택 PR의 새 SHA 원격 validator 결과 대기. 과거 성공 링크를 현재 PASS 근거로 쓰지 않음 |
| 실물/UI | 미검증 | 실물 MiniBig·새 proxy 보드·HA frontend UI 검증은 수행하지 않음 |

### 이번 실행 근거

- 표준 검사: `python -X utf8 <central>/scripts/check_integration.py . --check` 종료0. Windows 기본 cp949 대신 UTF-8로 실행합니다.
- `python -m ruff check .`, `python -m ruff format --check .`: 통과, 56 files. `git diff --check`: 통과.
- `actionlint 1.7.12 -shellcheck= -pyflakes=`: 모든 로컬 workflow 통과. shellcheck/pyflakes는 환경에 없어 별도 연동 미실행.
- `check_repository.py`는 공개 중앙 checkout 자체의 README 템플릿에서 `Header contains non-template content; migrate manually without loss`로 종료1입니다. 현재 통합의 `check_integration.py` 성공과 구분하며 중앙 원본은 수정하지 않았습니다. 기본 인코딩 실행의 cp949 오류를 확인한 뒤 `-X utf8`로 재실행한 실제 결과입니다.
- 현재 HA: WSL Ubuntu / Python3.14.7 / HA2026.10.2 / plugin0.13.373 / blesession0.9.0 / pycares5.2.0. 중앙 installer `INPUT_DEPENDENCY_MODE=current` 후 `python -m pytest tests/components/minibig/ -q`: **107 passed in 31.71s**, `pip check` 통과. 로그 `/tmp/minibig-current-pytest.log`, 환경 `/tmp/minibig-current-20261019`.
- 현재 HA × 라이브러리 정확한 하한: 별도 환경 `/tmp/minibig-current-minimum-20261019`, 같은 Python/HA/plugin/pycares 조합, 중앙 installer `INPUT_DEPENDENCY_MODE=minimum`, `INPUT_MINIMUM_PACKAGES='["blesession"]'`로 실제 blesession0.9.0 확인. **107 passed in 31.21s**, `pip check` 통과. 로그 `/tmp/minibig-current-minimum-install-20261019.log`, `/tmp/minibig-current-minimum-pytest-20261019.log`. current resolver 결과와 실제 설치값이 같아도 두 모드를 별도 환경에서 실행했습니다.
- 독립 현재 HA 재검증: review 담당이 전체 suite를 별도로 실행하여 **107 passed in 31.25s**, skip0·`pip check` 통과. 로그 `/tmp/minibig-independent-current-20261019.log`. 같은 환경에서 패키지 재설치 없이 실행했으며 중앙 통합 검사도 독립 종료0. 기존 테스트 함수105개 모두 AST 동일(누락0·수정0), 신규1개·총107cases 확인. 양언어 DOC-07 오류 단계·보고 키·추정 경로 의미를 실제 구현과 대조한 뒤 지적 해소 확인.
- 최소 HA × 라이브러리 정확한 하한(독립 review): `/tmp/minibig-review-min-20261019`, Python3.13.15 / HA2025.8.0 / plugin0.13.269 / blesession0.9.0 / pycares4.11.0. 중앙 installer minimum 모드로 정확한 하한 설치 후 **107 passed in 27.14s**, skip0·`pip check` 통과. 로그 `/tmp/minibig-independent-min-20261019.log`, 설치 `/tmp/minibig-review-min-install-zig4-20261019.log`.
- 최소 HA × current 라이브러리(root): 별도 `/tmp/minibig-minimum-current-20261019`, 같은 Python/HA/plugin/pycares 조합에서 current resolver도 blesession0.9.0 선택. **107 passed in 26.86s**, skip0·`pip check` 통과. 로그 `/tmp/minibig-minimum-current-install.log`, `/tmp/minibig-minimum-current-pytest.log`.
- 최소 HA 설치의 초기 실패는 WSL C 컴파일러 부재와 Zig의 Python 기본 linker 옵션 미지원이 원인이었습니다. 격리된 ziglang0.14.1의 CC와 `LDSHARED='...ziglang cc -shared'`로 ciso8601==2.3.2·lru-dict==1.3.0을 빌드한 뒤 중앙 installer가 성공했습니다. 시스템·리포·의존성 버전은 변경하지 않았으며 이후 환경도 같은 정확한 버전의 캐시 wheel을 사용했습니다.

### 게시와 남은 작업

승인 예외 및 독립 리뷰의 미해결 지적 없음. 로컬 적용·독립 검증 후 사용자 후속 요청에 따라 브랜치에 커밋·푸시하고 채택 PR로 제공합니다. PR 게시 후 정확한 SHA의 Tests/Validate 및 중앙 게시 현황을 별도로 확인해야 합니다. 중앙 원본 자체의 check_repository 실패는 위에 별도 기록했습니다.

## 2026-10-17 최초 채택 기록 (역사적 근거)

MiniBig 첫 채택의 실제 점검 기록입니다. 미완료 항목은 TODO로 유지합니다. [사용법과 판정 기준](https://github.com/eigger/hass-repo-standards/blob/b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0/docs/checklist.md)을 읽고, 아래 규칙은 `STANDARDS.md`에 기록한 표준 커밋에서 확인합니다. 태그·릴리스 대신 검토한 전체 커밋 SHA를 기준으로 합니다.

## 검토 대상

| 항목 | 값 |
|---|---|
| 통합 리포 / 실제 기본 브랜치 | `eigger/hass-minibig` / `main` |
| domain / 구현 경로 | `minibig` / `custom_components/minibig/` |
| 검토 대상 통합 커밋 / 채택 PR | 시작 `c45775cf2179ae052fa0b1a47543ada91807f50e` → 구현 main [`e70ee806dcbb8ebc561304253a8bbd373f9826b0`](https://github.com/eigger/hass-minibig/commit/e70ee806dcbb8ebc561304253a8bbd373f9826b0). 사용자 직접 push 지시, PR 없음. 이 마감 문서는 별도 후속 커밋으로 게시/검증 |
| 검토한 표준 전체 커밋 SHA | `b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0` |
| 검토일 / 조율 담당 | 2026-10-17 / root |
| 구현 서브 에이전트 / 독립 리뷰·검증 서브 에이전트 | minibig_implementation·minibig_docs / minibig_review |
| 중앙 현황표 반영일 / 기록 | 2026-10-17 시작 등록 [dbe3b96](https://github.com/eigger/hass-repo-standards/commit/dbe3b96a3b248fcf632e030a02a3c4f90a0e84a1) · [중앙 CI](https://github.com/eigger/hass-repo-standards/actions/runs/39041666477) 성공. 단계6e11e33 및 [구현·검증 종료 보고](https://github.com/eigger/hass-repo-standards/commit/b7b7d4cdf7df9b50bfd6405d3207873c1bb3f9e0) main 반영 |
| 변경 전 지원 최소 HA / 근거 파일(hacs.json·manifest·README) | 2025.8.0 — hacs.json.homeassistant·기존 양 README 일치. manifest는 별도 최소 선언 없음 |
| 유지·변경할 지원 최소 / 변경 시 실제 비호환 근거·명시적 승인 | 2025.8.0 유지; 통합0.3.0·blesession>=0.9.0 보존 |
| current 테스트 HA / 호환 Python·플러그인 | HA2026.10.2 / Python3.14.5 / 플러그인0.13.373; 로컬 실제 설치 확인 |
| 최소 테스트 HA / 호환 Python·플러그인 | HA2025.8.0 / Python3.13.14 / 플러그인0.13.269; 로컬 실제 설치 확인 |
| profile / 테스트 경로 | integration / ha · tests/components/minibig/ |
| 이전 검토 기록 | 최초 채택 |
| 채택 판정 | 구현 채택 필수 PASS/N/A, 예외/TODO 없음. 구현 main·정확한 SHA 원격CI·중앙 구현/검증 종료 보고 확인. 이 2문서 마감 커밋의 push/원격CI와 중앙 최종 완료 갱신은 별도 후속 확인 |

상태: `TODO` = 미확인·미충족, `PASS` = 근거로 확인, `EXCEPTION` = 적용 대상의 기록된 예외, `N/A` = 적용 조건에 해당 없음. 모든 항목은 미확인으로 시작합니다. `TODO`를 해당 없음으로 처리하지 않습니다. 묶은 규칙의 결과가 다르면 행을 나눕니다. 권장 항목은 별도로 표시했으며 미채택 이유를 기록합니다.

## 채택·구조·사용자 데이터

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| GOV-01, GOV-02 | `STANDARDS.md`에 표준 SHA·profile·실제 기본 브랜치·예외 기록, workflow/action은 검토 SHA로 고정 | PASS | [STANDARDS.md](STANDARDS.md) 기준 b1c80cf 전체 SHA·profile·main 기록. Tests/Validate/update_dependencies의 공통 호출 모두 해당 전체 SHA 고정. |
| GOV-03 | 새 표준 채택 변경의 영향·이관 방법과 명시적 채택 PR 확인. 규칙 자체를 변경하면 공통 CHANGELOG 기록 | PASS | 첫 명시적 채택이며 사용자 직접 push 지시로 검토한 diff를 반영. 기존 채택 기준 변경/중앙 규칙 변경 없음으로 후속 채택 PR·공통 CHANGELOG 변경 조건은 해당 없음. 영향은 STANDARDS·개발 문서에 기록. |
| GOV-04 | 중앙 표에 작업 시작·단계 변경·종료 상태, 담당·적용 내용·검증/리뷰 근거·남은 작업 갱신, 타 리포 기록 보존 | PASS | 시작 dbe3b96·단계6e11e33 및 [구현·검증 종료 보고 D](https://github.com/eigger/hass-repo-standards/commit/b7b7d4cdf7df9b50bfd6405d3207873c1bb3f9e0) 중앙 main 반영. 자기 행만 변경·타 기록 보존. D는 구현과 검증 종료의 실제 기록이며, 이 마감 문서 커밋 CI 확인 후 중앙 상태 문자열 완료를 갱신한다. |
| GOV-05 | 구현과 독립 리뷰·검증을 별도 서브 에이전트에게 위임, 지적 수정·재검증 및 결과 취합 | PASS | 구현 minibig_implementation/minibig_docs, 독립 minibig_review. 독립 양 HA 최종 106passed skip0·pip check 통과. 초기 상태·restore·부분 플랫폼 rollback·구독 취소·로그/문서 지적 수정 후 재검증. |
| HA-01, HA-13 | `custom_components/<domain>/`와 domain 일치, 필요한 모듈·공개 API·생명주기는 Core 대응 구조 | PASS | custom_components/minibig/와 실제 HA ConfigEntry/플랫폼·coordinator·runtime_data·async lifecycle 구조. 실제 manager 테스트 test_init/test_platforms 통과. |
| HA-02 | manifest 필드·정렬·동작 선언 확인, 공식 품질 등급 자가 표기 없음 | PASS | manifest domain minibig/name/config_flow/iot_class/local_polling·version0.3.0 보존, 실제 사용하는 HA bluetooth dependency로 정정. 공식 quality scale 선언 없음. [게시 SHA Validate](https://github.com/eigger/hass-minibig/actions/runs/39042575896)의 Hassfest 통과. |
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
| 구현 current HA × current/minimum BLE / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` 대응 freeze diff | Python3.14.5 / HA2026.10.2 / plugin0.13.373 | blesession0.9.0 양mode, extras/marker없음; pycares5.2.0 | 별도2venv sharedinstaller→pytest tests/components/minibig/ -q→pip check 각106passed skip0 | 실물/UI미검증 |
| 구현 minimum HA × current/minimum BLE / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` 대응 freeze diff | Python3.13.14 / HA2025.8.0 / plugin0.13.269 | blesession0.9.0 양mode, pycares4.11.0 | 별도2venv 동일명령 각106passed skip0·pip check | 실물/UI미검증 |
| 독립 current HA / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` 대응 freeze diff | Python3.14.5 / HA2026.10.2 / plugin0.13.373 | blesession0.9.0 / pycares5.2.0 | 독립env manifest/HA재귀설치→pytest tests/components/minibig/ -v 106passed skip0·pip check | 실물/UI미검증 |
| 독립 정확한 최소 HA / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` 대응 freeze diff | Python3.13.14 / HA2025.8.0 / plugin0.13.269 | blesession0.9.0 / pycares4.11.0 | 독립env pytest tests/components/minibig/ -v 106passed skip0·pip check | macOS asyncinotify 경고1(플랫폼차이); 같은 구현 SHA Linux CI는warning0 |
| 원격 current HA × current/minimum BLE / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` | Python3.14.8 / HA2026.10.2 / plugin0.13.373 | blesession0.9.0 양mode / pycares5.2.0 | [Tests39042575895](https://github.com/eigger/hass-minibig/actions/runs/39042575895) 각106passed skip0 warning0·pip check / lint2 PASS | 실물/UI미검증 |
| 원격 minimum HA × current/minimum BLE / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` | Python3.13.16 / HA2025.8.0 / plugin0.13.269 | blesession0.9.0 양mode / pycares4.11.0 | [같은 Tests](https://github.com/eigger/hass-minibig/actions/runs/39042575895) 각106passed skip0 warning0·pip check | macOS warning은 Linux 원격에서 없음 |
| 원격 HACS/Hassfest / PASS | `e70ee806dcbb8ebc561304253a8bbd373f9826b0` | 각 validator의 실제 원격 run | 브랜드 검사 포함, ignore없음 | [Validate39042575896](https://github.com/eigger/hass-minibig/actions/runs/39042575896) 양job 독립 PASS | UI표시/권리보증과 구별 |

## HACS·CI·의존성 업데이트

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| HACS-01, HACS-02 | 루트 README/LICENSE/hacs.json, 검증한 최소 HA, 실제 배포 구조와 필요한 옵션 일치 | PASS | 루트 README/LICENSE/hacs.json, custom_components/minibig 배포. hacs.homeassistant2025.8.0 유지·실제 최소106tests통과, 불필요 zip/content 옵션 추가 없음. |
| HACS-03, HACS-05 | Default 여부는 목록 근거로 확인, [로컬 brand/icon.png 또는 원격 brands 근거](https://github.com/eigger/hass-repo-standards/blob/b1c80cf2c4bf8b4bc4e3556409ad948b7f850ea0/docs/hacs.md)와 HACS/Hassfest 실제 실행, ignore는 이유·해제 조건 기록 | PASS | HACS Custom 표기. 기존 brand/icon 실제PNG256×256 RGB, 기존512×512를 icon@2x로 보존; logo444×128 RGBA 유지. 기존출처 e205ba1·MIT·권리한계 development 기록. [정확 구현 SHA Validate39042575896](https://github.com/eigger/hass-minibig/actions/runs/39042575896) 브랜드 포함 HACS·Hassfest 독립 PASS; ignore 없음. |
| HACS-06 (권장) | description·topics·issue 경로·brands 및 사용하는 HACS 필드 지원 확인 | PASS | 실제 원격 Issues/Discussions·MIT·main·정식 v0.3.0 확인. 로컬 brand 실형식 확인; description/topics 설정은 이번 범위에서 변경하지 않음. 임의 HACS 필드 없음. |
| CI-01, CI-02 | Validate/Python Tests 공통화, 확장 job 유지, PR·실제 기본 브랜치 push·dispatch 및 필요한 schedule | PASS | Tests·Validate·Update dependencies 중앙재사용으로 통합. Tests/Validate는 mainpush·PR·dispatch·schedule, updater는 weekly/dispatch. 기존 별도 UI/build job 없음. |
| CI-03, CI-05, CI-08 | 최소 권한·checkout 자격증명 비보존·timeout·concurrency, full SHA·갱신 관리, 비신뢰 입력·secrets 경계 | PASS | caller contents:read, updater job만 contents/PRwrite. 중앙 pin b1c80cf·actions fullSHA·checkout credentials비보존·timeout/concurrency·bot비취소. Dependabot 액션갱신, untrusted PR metadata shell직삽입/secrets inherit 없음. |
| CI-04, CI-07, CI-12 | 실패를 숨기지 않는 실제 `ha` 필수 테스트, 버전별 환경·cache·Ruff 설정과 required checks 이름 확인 | PASS | ha 필수·최소/current HA×BLE 네 matrix, lint별도; 실패은폐/skip없음, cache와 requirements/manifest 포함. 원격 branch protection404/rulesets[]라 기존 required check 없음·설정변경없음. 정확 구현 SHA 원격 Tests의4matrix·lint2 모두성공, 환경표 참조. |
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
| 없음 | 구현 main 및 해당 SHA 원격 독립 검증과 중앙 종료 근거 확인. 적용 필수 EXCEPTION 없음 | root | 후속 규칙/구현 변경 시 재검토 |

| 규칙 ID / TODO | 남은 작업 / issue·PR | 담당자 | 완료 근거 |
|---|---|---|---|
| 현재 적용 필수 TODO 없음 | 구현 e70ee806과 중앙 종료 D 확인; 이 마감 문서 push·문서 SHA CI·중앙 최종 상태 갱신은 조율 단계에서 후속 확인 | root·minibig_review | 구현 Test/Validate·중앙 종료 링크 위 참조 |

최종 검토 시 적용 대상 필수 `TODO`와 `EXCEPTION`, 이유가 있는 `N/A`, 권장 미채택을 구분해 적습니다. CI 성공만으로 실물 기기 검증을 주장하지 않습니다. 실물 검증을 수행했다면 모델·펌웨어·어댑터/proxy·연결 경로와 결과를 별도로 기록합니다.

중앙 보고는 [적용 현황표](https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md)의 자기 리포 행에 반영합니다. 리뷰 지적·수정·재검증 결과와 중앙 갱신 실패 사유가 있으면 남은 작업에도 기록합니다.

## 검증 기록 세부

2026-10-17 최종 구현 freeze 후 구현 담당 네 격리 환경과 독립 리뷰 담당 두 격리 환경에서 동일 tree의 actual HA 106cases 모두 통과했습니다. 기존 79함수 모두 보존, 최종105함수(한 파라미터 추가로106cases), skip0입니다. 신규 coverage는 실제 setup/flow/options·registry/state/actions·저장identity·stale정리·광고자가복구·live/restore양분기·실제partialforwardrollback·subscribe취소·coordinator생성자실패전구독미취득·오류진단·number DPoverride입니다. select는 기존 프로필 모두 enum값 미측정으로 노출하지 않는 조건을 확인했으며 미구현 선택값을 만들어 지원으로 주장하지 않습니다.

명령: docs/development.md의 INPUT_DOMAIN=minibig·ha profile·각 requirements·expected HA·ha-components로 shared installer(bootstrap pip/packaging, RUNNER_TEMP 별도), 구현 환경에서 `python -m pytest tests/components/minibig/ -q`, 독립 환경에서 `python -m pytest tests/components/minibig/ -v`, 양쪽 `python -m pip check`. 최소/current 라이브러리는 별도 환경으로 설치했습니다. Ruff check/format(49files), actionlint(shellcheck/pyflakes별도비활성), diffcheck PASS. 독립 updater PyPI dry-run은 blesession0.9.0 변경없음. `sync_badges.py --check`, 로컬파일링크 누락0, 중앙 check_repository 26문서7workflow PASS. 설치/린트와 실제HA성공은 구별하며 위 원격 결과는 실제 게시된 구현 SHA e70ee806의 근거입니다. 이 마감 문서의 미래 SHA/CI를 추정하지 않습니다.

브랜드는 초기 e205ba10b4616c28db8aa9f538b928d6b1ef5697의512 PNG icon을 icon@2x로 보존하고256 icon을 추가했습니다. logo444×128 RGBA는 보존. 출처·기존MIT와 권리/표시 한계는 development에 기록했습니다. 실물·새프록시보드·HA frontend UI는 미검증이며 과거README CLWM-B06관측과 분리합니다.

최종 추가 경계 수정 뒤 독립 재검증: current106passed27.06s, minimum106passed26.07s(skip0)·양 pip check PASS. 구현 네 환경도 각106passed. 독립 로그 `/tmp/minibig-review-current-final2.log`, `/tmp/minibig-review-min-final2.log` (로컬 검증 이력; 구현 SHA 원격 증거는 위 환경표에 별도 기록).

원격 Tests current/current job117424851899·current/minimum117424851894·minimum/current117424851913·minimum/minimum117424851940 및 lint117424851782/117424851933를 독립 검토했습니다. 네 matrix의 실제 설치값·pip check·106passed/skip0/warning0과 Validate HACS117424851847/Hassfest117424851640 성공을 확인했습니다. 이후 마감 문서 커밋은 이 문서와 STANDARDS 두 파일만 변경하며 별도 자동 CI 결과를 조율자가 확인하고 중앙 최종 행에 실제 링크를 기록합니다.
