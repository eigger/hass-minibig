# MiniBig Bluetooth 문제 해결

[English](troubleshooting.md) · [README](../README.ko.md) · [상세 사용](usage.ko.md)

## 모델·초기 준비

광고에서 판별한 실제 프로필·펌웨어·하드웨어 리비전을 확인합니다. Window Opener, 신형/구형 PushMini, SwitchMini, HubMini는 기능이 다릅니다. 구형 PushMini에는 배터리 DP가 없습니다. Unknown 프로필에 임의의 제어 DP를 부여하지 않으며 HubMini는 불필요하고 지원하지 않습니다. 기존 [CLWM-B06 프로토콜 관측](BLE_PROTOCOL.md)은 과거 기록으로, 이번 공통화의 새 실물 검증이 아닙니다.

창문 오프너는 공식 앱에서 설치 유형·개폐 방향·이동 한계 캘리브레이션을 먼저 완료합니다. 통합이 모든 모델의 설치/캘리브레이션 DP를 식별하지는 않습니다. 연결 문제를 해결하려고 DP를 추측하지 마세요. 이동 경로를 비우고 동작을 지켜보며, 창문 주변에 사람이 있을 때 재시작·공장 초기화·raw 쓰기를 실행하지 마세요. 전원/충전·깨우기·페어링은 해당 모델 설명서를 따릅니다. 공통 본딩·초기화 절차를 가정하지 않습니다.

## 광고 발견과 GATT 연결 구별

[Bluetooth 프록시 설정](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.ko.md)을 따르세요. XIAO W5500와 USB-A 동글 형태 AtomS3U 추천은 공통 안내이며, 이번 작업에서 MiniBig과 새로 실물 검증한 기기가 아닙니다.

1. HA Bluetooth와 사용할 로컬 어댑터/프록시가 온라인이고 전원·거리가 적절한지 확인합니다. 금속 창틀과 프록시 네트워크 끊김도 수신에 영향을 줍니다.
2. 광고부터 확인합니다. passive coordinator는 HA `BluetoothScanningMode.ACTIVE`를 요청합니다. active scan은 광고의 scan response를 요청하는 기능이며, active GATT 연결을 허용하는 ESPHome `bluetooth_proxy.active`와 다릅니다. 광고가 보여도 연결 가능한 경로나 빈 GATT 슬롯이 있다는 뜻은 아닙니다.
3. 공식 앱·다른 BLE central 연결을 해제하고 전원이 켜진 기기를 가까이 둡니다. 깨우기/페어링 방법은 모델 설명서를 따르고 실제 pairing 진단 상태를 확인하세요. ESL의 깨우기 절차를 복사하지 않습니다.
4. 연결 슬롯과 다른 연결 기기를 확인합니다. **연결 유지** 기본값은 꺼짐입니다. 켜면 기기의 단일 BLE 연결을 점유해 앱 연결을 막을 수 있습니다. 일반 세션은 유휴 시간(기본 30초)이 지나면 끊으므로 명령 사이 disconnected 표시는 정상일 수 있습니다.
5. 경쟁 연결을 해제한 뒤 일반 엔티티 동작을 재시도합니다. 경로·슬롯 확인 대신 모르는 raw 명령을 반복하거나 HA를 계속 재시작하지 마세요.

## 실제 진단 항목 해석

- **범위 안**은 광고 존재, **연결됨**은 현재 GATT 링크입니다. 개별 명령의 성공을 보장하지 않습니다.
- **이동 중**은 보고 패킷에 따라 바뀝니다. 이동 중에는 폴링을 건너뜁니다. `poll_interval_min=0`은 주기적 폴링만 끄며 사용자 명령·push 보고를 끄지 않습니다.
- **마지막 실패**, **오류 횟수**, **연결 시간**은 BLE 세션 결과입니다. 실패 속성의 operation/stage·추정 원인·어댑터/프록시 경로(`via`, RSSI, paths)·단계 시간·오류를 확인합니다. 범위 밖 상태 폴링 실패는 명령 실패 횟수에 포함하지 않습니다.
- 프로필/프로토콜 매핑과 무선 연결 문제를 구별합니다. 끝점이 97%처럼 표시돼도 기존 관측에서는 앱과 같은 값이므로 통신 실패로 단정하지 않습니다. `power_dp_id`, `position_dp_id`, 이름별 `dp_overrides`는 모델에서 확인된 매핑이 필요합니다. select는 raw enum 매핑도 필요하여 DP override만으로 모든 선택 엔티티가 생기지는 않습니다.

확인된 DP 탐색만 [raw 작업 예시](usage.ko.md#커스텀-또는-미지원-dp-id-탐색)를 따릅니다. `minibig.send_raw`의 `device_id`는 target이 아닌 **data** 필드입니다. 응답은 **개발자 도구 → 이벤트 → `minibig_raw_response`**에서 수신합니다. 이벤트에는 의도적으로 기기 ID/주소·method·status·raw data·성공 여부가 있습니다. 응답이 있어도 기계적 캘리브레이션이 맞다는 뜻은 아닙니다. 일상 제어는 일반 엔티티를 사용하세요.

## 안전한 제보

재현 중에만 `custom_components.minibig: debug`를 켜고 이후 해제하세요. 디버그 프로토콜 로그·BLE 실패 센서 속성·raw 이벤트에는 Bluetooth 주소, 프록시 주소/이름/경로, 식별 바이트, 물리 위치, 패킷과 세션 시간이 들어갈 수 있습니다. 로컬 진단값을 그대로 공개하면 안 됩니다.

[이슈](https://github.com/eigger/hass-minibig/issues) 등록 전에 주소·기기/entry ID·프록시 이름/IP·raw payload·민감한 상태를 제거/가림 처리합니다. 필요한 opcode·오류 종류·단계·비식별 처리한 시간은 남길 수 있습니다. HA/통합/blesession 버전·모델/펌웨어·로컬 어댑터 또는 프록시 모델/펌웨어·연결 유지/폴링 설정·재현 순서와 실패 단계(발견/GATT/응답/실제 이동)를 적습니다. 전체 HA 설정이나 미처리 이벤트 덤프, 인증정보·키를 공개하지 마세요.

실제 HA 자동 테스트는 외부 BLE 경계에서 통합 동작을 검증합니다. 물리 기구·모든 모델/펌웨어·새 프록시 보드·frontend UI를 검증하지는 않습니다.
