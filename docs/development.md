# 개발·실제 HA 테스트

[English README](../README.md) · [한국어 README](../README.ko.md) · [적용 체크리스트](../ADOPTION_CHECKLIST.md)

이 통합은 `custom_components/minibig/`로 배포하는 HACS 커스텀 통합입니다. Core에 대응하는 모듈·config entry 생명주기·공개 API 구조이며 공식 Core 포함/품질 등급을 주장하지 않습니다. 프로토콜·광고·GATT는 `minibig_ble/`, HA 상태/엔티티는 coordinator와 플랫폼 모듈, BLE 보고는 `session_report.py`, raw/DP 작업은 `services.py`로 분리합니다.

## 테스트 경계·지원 정책

테스트는 Core와 같은 `tests/components/minibig/`에 배치하고 `tests/conftest.py`의 중앙 원본과 동일한 autouse fixture `auto_enable_custom_integrations`가 커스텀 통합을 활성화합니다. domain conftest의 `mock_config_entry`와 `mock_client`는 실제 entry와 외부 BLE transport fixture를 제공합니다. `hass`, `enable_custom_integrations`, 실제 HA 테스트 helper `MockConfigEntry`로 loader·entry·플랫폼·registry·상태을 검증하며 외부 Bluetooth 광고/GATT 통신 경계만 대체합니다. HA core stub·FakeHass·`--no-deps`로 대신하지 않습니다. 기존 parser·writer·연결·coordinator·보고·서비스 회귀 검사는 유지합니다.

| 환경 | Python | HA | pytest-homeassistant-custom-component | requirements |
|---|---|---|---|---|
| 기존 지원 최소 보존 | 3.13 | 2025.8.0 | 0.13.269 | `requirements_test_min.txt` |
| current | 3.14 (3.14.2 이상) | 2026.10.2 | 0.13.373 | `requirements_test.txt` |

이 표는 목표 조합입니다. 실제 실행 버전·검증 결과·대상 commit은 체크리스트가 원본입니다. `hacs.json.homeassistant=2025.8.0`은 지원 선언이며 current 테스트 최신화와 별개입니다. 최신 HA 실패는 호환 문제를 수정하고 최소 테스트를 보존합니다. 실제 비호환 근거와 별도 명시적 사용자 승인 없이 하한을 올리지 않습니다. 최소 HA의 aiodns 3.5가 사용하는 pycares 4.x API를 보존하기 위해 `requirements_test_min.txt`에 테스트 전용 `pycares==4.11.0`을 고정합니다. 이는 런타임 manifest 의존성 추가나 지원 최소 상향이 아닙니다. 과거 최소 requirements와 `constraints/**`는 Dependabot에서 제외하고 current HA·플러그인을 호환 그룹으로 검토합니다. 최소 파일 혼합 갱신·다운그레이드·expected HA/Python 불일치를 자동 병합하지 않습니다.

## 새 가상환경에서 실행

최소/current HA와 최소/current 라이브러리의 네 조합은 각각 별도 환경으로 만드세요. 중앙 표준 checkout은 `STANDARDS.md`의 전체 SHA를 사용하고 `STANDARDS_CHECKOUT`을 실제 경로로 바꿉니다. 깨끗한 current 예시:

```bash
python3.14 -m venv .venv-current
source .venv-current/bin/activate
python -m pip install --upgrade pip packaging
STANDARDS_CHECKOUT=/path/to/hass-repo-standards
INPUT_DOMAIN=minibig \
INPUT_REQUIREMENTS=requirements_test.txt \
INPUT_HA_COMPONENTS='bluetooth sensor binary_sensor button switch cover select number' \
INPUT_TEST_PROFILE=ha \
INPUT_EXPECTED_HA_VERSION=2026.10.2 \
INPUT_DEPENDENCY_MODE=current \
RUNNER_TEMP="$(mktemp -d)" \
python "$STANDARDS_CHECKOUT/actions/python-environment/install.py"
python -m pytest tests/components/minibig/ -v
python -m pip check
```

정확한 최소 HA는 Python 3.13의 새 환경에서 `INPUT_REQUIREMENTS=requirements_test_min.txt`, `INPUT_EXPECTED_HA_VERSION=2025.8.0`로 실행합니다. 각 HA의 라이브러리 최소 조합은 다시 새 환경을 만들고 위 installer에 `INPUT_DEPENDENCY_MODE=minimum`과 `INPUT_MINIMUM_PACKAGES='["blesession"]'`를 지정합니다. 최소/current 축을 한 환경의 재설치로 혼합하지 말고 각각 pytest·pip check를 수행합니다. manifest의 `blesession>=0.9.0` 하한은 **0.9.0** 실제 설치로 확인합니다. current resolver가 현재 같은 값을 선택해도 두 모드는 별도 검증입니다.

```bash
python -m pip install -r requirements_lint.txt
python -m ruff check .
python -m ruff format --check .
python -c "from importlib.metadata import version; print({p: version(p) for p in ('homeassistant', 'pytest-homeassistant-custom-component', 'blesession')})"
```

원격 [Tests](../.github/workflows/tests.yml)의 matrix/입력, 기존 매주 월요일 검사를 보존한 [Scheduled tests](../.github/workflows/scheduled_tests.yml), [Validate](../.github/workflows/validate.yml)의 HACS·Hassfest 결과를 대상 SHA별 확인합니다. CI 성공으로 실물 MiniBig·HA frontend UI·새 프록시 보드 검증을 주장하지 않습니다.

## 의존성·문서 변경

런타임 패키지는 manifest requirements, HA domain은 dependencies/after_dependencies, 테스트·린트 도구는 별도 requirements에 둡니다. [공통 의존성 추가 절차](https://github.com/eigger/hass-repo-standards/blob/0bfb572cbe49b92b3dbc559382c00bd0eb2cbd44/docs/dependencies.md)에 따라 extras·marker·연산자·호환 플랫폼·라이선스와 최소/current HA 설치를 검토합니다. bot은 새 하한 tree를 검증한 후 PR로 제안하며 실패를 숨기지 않습니다. GITHUB_TOKEN으로 만든 PR은 후속 push/PR CI를 자동 실행한다고 가정하지 않으며 추가 required checks는 수동 dispatch 등 별도 운영으로 확인합니다.

README는 영어/한국어 빠른 시작을 유지하고 상세 사용·문제 해결은 docs에 보존합니다. 배지는 `.hass-standards.json`과 관리 주석으로 양쪽을 함께 갱신합니다. 중앙 checkout의 `python3 scripts/check_integration.py /path/to/hass-minibig --check`로 확인합니다. Usage는 Analytics 조회 성공 여부와 무관하게 실제 domain `minibig`를 사용합니다. 로그·fixture 공개 전 주소/기기 ID/프록시 정보/raw payload/민감한 물리 상태을 제거하세요.

## 기존 브랜드 자산

브랜드 파일은 기존 리포 초기 커밋 `e205ba10b4616c28db8aa9f538b928d6b1ef5697`에서 들어온 자산이며 루트 MIT LICENSE와 기존 이력을 기록합니다. 최초 icon은 PNG512×512 RGB, logo는 PNG444×128 RGBA였습니다. 최종 icon은 PNG256×256 RGB이며 기존512×512 원본은 icon@2x.png로 보존합니다. logo444×128 RGBA는 유지합니다. 원격 브랜드 검사 결과는 체크리스트에서 확인합니다. 이 기록은 제조사의 별도 권리 허가나 HA brands 공식 등록을 새로 보장하지 않습니다. HA2026.3 이전 지원 환경의 로컬 아이콘 UI 표시를 검증했다는 뜻도 아닙니다.

## 사용자 영향과 검증 한계

기존 domain·entry schema·unique ID와 최소 지원을 보존합니다. 외부 BLE 계층의 lifecycle 보완이 있으면 체크리스트에 실제 회귀 테스트와 대응 변경을 남깁니다. 디버그/raw 이벤트와 진단 속성은 로컬에서 유용하지만 공개 전에 비식별 처리해야 합니다. 물리 창문·캘리브레이션·공장 초기화는 자동 테스트만으로 안전성을 보장하지 않습니다. 이번 공통화 자체로 태그·릴리스를 생성하지 않습니다.
