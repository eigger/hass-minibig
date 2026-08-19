# MiniBig BLE for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/eigger/hass-minibig.svg)](https://github.com/eigger/hass-minibig/releases)
[![HACS Default](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**MiniBig** BLE 기기를 클라우드 없이 로컬에서 직접 제어하는 Home Assistant 커스텀 통합 구성요소입니다.

[English README](README.en.md)

---

## 지원 기기

| 기기 | 타입 식별자 | 기능 | 지원 플랫폼 |
|---|---|---|---|
| **Window Opener** (창문 오프너) | Generic (`d_type != 1, 2`) | 목표 위치 (0~100%), 정지, 배터리, 실시간 이동 스트리밍 | `cover`, `sensor`, `binary_sensor`, `button` |
| **PushMini (신형)** | `d_type = 1` | 켜기/끄기 (`dp0`), 배터리 (`dp10`), 재시작, 공장 초기화 | `switch`, `sensor`, `binary_sensor`, `button` |
| **PushMini (구형)** | `d_type = 1` + 레거시 조건 | Action / Setting 비트필드, 재시작, 공장 초기화 | `switch`, `sensor`, `binary_sensor`, `button` |
| **SwitchMini** (스위치미니) | `d_type = 1` / Switch | 켜기/끄기, 배터리, 커스텀 DP ID 주입 | `switch`, `sensor`, `binary_sensor`, `button` |
| **HubMini** (허브미니) | `d_type = 2` | 외부 게이트웨이 — HA에서는 **불필요** | *지원하지 않음* (HA가 BLE로 직접 연결) |

---

## 주요 특징

- **100% 로컬 GATT 제어**: 계정 로그인이나 클라우드 없이 빠르고 직접적인 Bluetooth GATT 통신.
- **온디맨드 연결 및 자동 해제**: 필요 시 연결하고 30초 유휴 후 자동으로 BLE 슬롯을 해제, 공식 앱과의 공존 및 배터리 절약.
- **정확한 위치 보고**: 공식 앱과 동일한 위치값 보고 — 끝점에서 임의로 반올림하지 않음.
- **실시간 이동 추적**: `REPORT_DPS` (opcode 24) 라이브 푸시 패킷으로 과도한 폴링 없이 이동 상태를 부드럽게 추적.
- **명령 병합**: 연결 설정 중 또는 실행 중에 들어온 연속 명령은 자동으로 최신 명령으로 병합되어 모터에 마지막 의도된 상태만 전달.
- **슬롯 고갈 복구**: 오래된 연결과 단일 슬롯 제한을 재시도 및 복구 로직으로 자동 처리.

---

## 설치

### HACS를 통한 설치 (권장)

1. Home Assistant에서 **HACS**를 엽니다.
2. 우측 상단 메뉴(점 세 개) → **Custom repositories** 클릭.
3. 저장소 URL `https://github.com/eigger/hass-minibig` 를 카테고리 **Integration**으로 추가.
4. HACS에서 **MiniBig**을 검색하여 **Download** 클릭.
5. Home Assistant를 재시작합니다.

### 수동 설치

1. `custom_components/minibig` 폴더를 Home Assistant `<config_dir>/custom_components/` 디렉터리에 복사합니다.
2. Home Assistant를 재시작합니다.

---

## 설정

MiniBig 기기의 전원을 켜면 Home Assistant 블루투스가 자동으로 기기를 발견합니다. 알림에서 **구성**을 클릭하여 추가하세요.

### 옵션

통합 기기 설정에서 **구성**을 클릭하여 조정할 수 있습니다:

- **연결 유지** (`keep_connected`): 지속적인 BLE 연결을 유지합니다.
  > **주의**: 활성화하면 공식 스마트폰 앱의 연결이 차단되고 기기 배터리 소모가 증가합니다. 기본값은 **비활성화**.
- **폴링 간격** (`poll_interval_min`): 백그라운드 상태 폴링 간격(분, 기본: 30분, `0`으로 설정 시 주기적 폴링 비활성화). 기기가 이동 중일 때는 폴링을 건너뜁니다.
- **연결 재시도 횟수** (`retry_count`): 초기 연결 실패 시 재시도 횟수 (기본: 3).
- **커스텀 DP ID**: 미확인 하드웨어 변형이나 테스트를 위해 `power_dp_id` 또는 `position_dp_id`를 직접 지정할 수 있습니다.

---

## 확인된 DP 매핑

실제 하드웨어(CLWM-B06 창문 오프너)에서 각 동작을 개별 격리하고 `READ_DPS` 덤프를 비교하여 확인:

| DP ID | 기능 | 상태 |
|---|---|---|
| `0` | 위치 (창문 오프너) / 전원 (PushMini, SwitchMini) | ✅ 확인 — 공식 앱과 완전히 일치 |
| `3` | 정지 (이동 없이 수동 위치 폴링에도 사용 가능) | ✅ 확인 |
| `10` | 배터리 퍼센트 | ✅ 확인 |

이 세 가지 DP ID로 통합이 제어·보고하는 모든 것을 커버합니다. 기기에는 다른 DP ID도 존재하지만 공식 앱의 최초 설치 마법사(설치 유형, 개폐 방향, 이동 한계 캘리브레이션)에서만 사용되므로 이 통합에서는 노출하지 않습니다. 자세한 내용은 [`docs/BLE_PROTOCOL.md`](docs/BLE_PROTOCOL.md#42-modern-dp-data-point-triplet-format)를 참고하거나, 아래 `minibig.send_raw`를 직접 사용해 탐색하세요.

---

## 커스텀 또는 미지원 DP ID 탐색

새로운 기기 변형의 DP ID를 발견하려면:

1. **개발자 도구 → 작업**에서 `minibig.send_raw` 서비스를 호출합니다:
   ```yaml
   action: minibig.send_raw
   target:
     device_id: <기기_ID>
   data:
     method: 43  # 43 = READ_DPS
     payload: ""
   ```
2. Home Assistant 로그에서 응답을 확인하거나 **개발자 도구 → 이벤트**에서 `minibig_raw_response` 이벤트를 수신합니다.
3. 응답에는 `[dpId (1바이트)][값 (2바이트 BE)]` 트리플릿이 반복되어 기기의 모든 활성 DP가 표시됩니다.

---

## 기술 문서

- [BLE 프로토콜 명세](docs/BLE_PROTOCOL.md): GATT 서비스, 패킷 레이아웃, 암호화 키, opcode에 대한 완전한 기술 명세.
- [아키텍처 및 설계](docs/ARCHITECTURE.md): 컴포넌트 레이어링, 코디네이터 상태 흐름, 트랜잭션 관리 설계.

---

## 디버그 로깅

상세 프로토콜 디버깅을 활성화하려면 `configuration.yaml`에 다음을 추가합니다:

```yaml
logger:
  default: info
  logs:
    custom_components.minibig: debug
```

---

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다 — 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.
