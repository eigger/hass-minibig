<!-- hass-standards:header:start -->
# MiniBig BLE for Home Assistant

MiniBig 창문 오프너와 PushMini/SwitchMini를 클라우드 계정·HubMini 없이 로컬 Bluetooth GATT로 제어하는 HACS 커스텀 통합입니다.

[English](README.md) | **한국어**

<!-- hass-standards:badges:start -->
[![Release](https://img.shields.io/github/v/release/eigger/hass-minibig?style=flat)](https://github.com/eigger/hass-minibig/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat)](#설치)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.8.0-41BDF5?style=flat)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-minibig/tests.yml?branch=main&style=flat&label=Tests)](https://github.com/eigger/hass-minibig/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-minibig/validate.yml?branch=main&style=flat&label=Validate)](https://github.com/eigger/hass-minibig/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-minibig?style=flat)](LICENSE)
[![Analytics reporting installs](https://img.shields.io/badge/dynamic/json?style=flat&color=41BDF5&label=Usage&query=%24.minibig.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)](https://analytics.home-assistant.io/)
<!-- hass-standards:badges:end -->
<!-- hass-standards:header:end -->

## 기기와 기능

- 창문 오프너: 위치·정지·이동 상태·배터리.
- PushMini: 신형/구형 프로필에 따라 기능이 다릅니다. SwitchMini 전원 제어에는 확인된 DP 재정의가 필요할 수 있습니다.
- 연결·범위·실패·연결 시간 진단 센서. 미확인 기기는 프로필에서 확인된 기능만 제공하며 HubMini는 추가를 거부합니다.

[기기별 프로필·옵션·프로토콜 상세](docs/usage.ko.md)를 확인하세요. 구형 PushMini에는 배터리 DP가 없으며 펌웨어 변형을 같은 기기로 간주하면 안 됩니다.

## 요구사항

Home Assistant **2025.8.0 이상**, 기기 범위 안의 연결 가능한 Bluetooth 어댑터/프록시가 필요합니다. `blesession`은 HA가 자동 설치합니다. 최초 설치 유형·방향·이동 한계 캘리브레이션은 공식 앱에서 마치고, HA 제어 전 앱 연결을 해제하세요.

프록시 설정·추천 기기는 [Bluetooth 프록시 설정](https://github.com/eigger/blesession/blob/main/docs/bluetooth.ko.md)을 따릅니다. 광고 스캔과 active GATT 연결은 다른 조건입니다.

## 설치

1. HACS 사용자 지정 저장소에 `https://github.com/eigger/hass-minibig`를 **Integration** 유형으로 추가합니다.
2. **MiniBig**을 다운로드하고 HA를 재시작합니다. 수동 설치는 `custom_components/minibig`를 `<config_dir>/custom_components/`로 복사하고 재시작합니다.
3. 가까이에서 기기 전원을 켜고 Bluetooth 발견 알림을 구성하거나 **설정 → 기기 및 서비스**에서 **MiniBig**을 추가합니다.
4. 생성된 cover/switch를 사용합니다. 예를 들어 **개발자 도구 → 작업**에서 창문 엔티티에 `cover.stop_cover`를 호출하면 이동을 멈춥니다.

## 중요 제한

창문 이동 경로를 비우고 물리 모터 동작을 지켜보세요. raw 명령·공장 초기화·미확인 DP 재정의는 캘리브레이션을 변경하거나 기기를 움직일 수 있으므로 확인된 모델 매핑에만 사용합니다. **연결 유지** 기본값은 꺼짐입니다. 켜면 BLE 연결을 점유하여 공식 앱 연결을 막거나 배터리 사용량을 늘릴 수 있습니다. 배터리 보고 여부는 프로필에 따라 다릅니다.

기존 CLWM-B06 실물 관측은 상세 문서에 보존했습니다. 이번 공통화는 새 실물·프록시 보드·HA UI 검증을 뜻하지 않습니다. Usage는 데이터 제공에 동의한 HA Analytics 참여 설치 집계이며 미집계·조회 실패는 설치 수 0이 아닙니다.

## 문서

- [사용·프로필·옵션·raw 작업](docs/usage.ko.md) · [English](docs/usage.md)
- [Bluetooth 문제 해결·안전한 제보](docs/troubleshooting.ko.md) · [English](docs/troubleshooting.md)
- [BLE 프로토콜 (영문)](docs/BLE_PROTOCOL.md) · [아키텍처 (영문)](docs/ARCHITECTURE.md)
- [개발·실제 HA 테스트·의존성](docs/development.md)
- [공통 규칙·검증 기록](STANDARDS.md)

주소·기기 ID·raw 이벤트 payload·민감한 물리 상태는 로그 공개 전에 제거하세요.

<!-- hass-standards:support:start -->
## 지원

- [Issues](https://github.com/eigger/hass-minibig/issues): 버그를 신고하거나 기능을 요청하세요.
- [Discussions](https://github.com/eigger/hass-minibig/discussions): 질문하고 사용 경험을 공유하세요.
<!-- hass-standards:support:end -->

<!-- hass-standards:related-projects:start -->
<!-- hass-standards:related-projects:end -->

<!-- hass-standards:license:start -->
## 라이선스

[MIT License](LICENSE) 라이선스로 배포됩니다.
<!-- hass-standards:license:end -->
