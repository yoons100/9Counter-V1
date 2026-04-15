![Platform](https://img.shields.io/badge/platform-Windows-blue) [![Release](https://img.shields.io/badge/Release-V1.7-fc1ba6)](https://github.com/Yoons-B1/9Counter-V1/releases) ![License](https://img.shields.io/github/license/Yoons-B1/9Counter-V1)
# <img width="36" height="36" alt="9icon copy" src="https://github.com/user-attachments/assets/59fa5943-f3d1-48b7-9af0-5323b2ed6037" /> 9Counter V1

---

## ✨ 9Counter V2.0 Update

9Counter has been updated to **V2.0**, introducing an official Multi-Counter Launcher system.

### New Features
- Control multiple counters using the **Counter Launcher** system
- Added **NDI output support** alongside SPOUT and OSC  
  → Now compatible with tools like **vMix, Resolume, and MadMapper**
- Improved **time logic stability**

### Availability
The V2.0 version is now available on the Microsoft Store :  
https://apps.microsoft.com/detail/9PCXK61XCCQN

* The app is listed as a low-cost paid version.  
If you need a **redeem code**, feel free to contact me :  
antonio@credl.net

---

## ✨ 9Counter V2.0 업데이트

9Counter가 멀티 카운터를 공식 지원하는 Launcher 기능을 추가하여  
**V2.0**으로 업데이트되었습니다.

### 주요 기능
- **Counter Launcher 방식**으로 여러 개의 카운터를 동시에 제어
- 기존 SPOUT, OSC에 더해 **NDI 출력 지원 추가**  
  → vMix, Resolume, MadMapper 등과 연동 가능
- **타임 로직 안정화**

### 다운로드
V2.0 버전은 Microsoft Store에서 다운로드할 수 있습니다 :  
https://apps.microsoft.com/detail/9PCXK61XCCQN

* 소액 유료 앱으로 등록되어 있지만,  
**리딤코드**가 필요하신 경우 메일로 요청하시면 보내드립니다.  
antonio@credl.net

---

## 9Counter V1 Overview

9Counter is a count-up timer with configurable start and end time.

It supports millisecond display, Spout video output, and OSC remote control.
It also includes an option to display time beyond 24 hours.

---

## Features

*  Count-up timer (supports 24+ hours display)
*  Start / End time configuration
*  Font, color, and outline settings (Spout)
*  Borderless / Always-on-top mode
*  Spout output (with alpha transparency)
*  OSC remote control (Play / Stop)

---

## Usage

### Basic Controls

| Key      | Function             |
| -------- | -------------------- |
| Space    | Play / Pause         |
| S        | Stop / Reset         |
| F        | Fullscreen           |
| ESC      | Exit Fullscreen      |
| F2       | Open Settings        |
| T        | Toggle Always on Top |
| B        | Toggle Borderless    |
| Ctrl + Q | Quit                 |

---
<img width="671" height="211" alt="2026-04-10 13 14 53" src="https://github.com/user-attachments/assets/e53a6181-5b2b-4b53-9229-446ac2f27c5f" />  

<img width="671" height="661" alt="setup" src="https://github.com/user-attachments/assets/1ae213ad-c3f0-4d4f-8f13-448ea38a4d4a" />


### Settings

Press **F2** to open settings.

* Start Time / End Time
* Show milliseconds
* Continuous hours (24+)
* Font / Color / Outline
* Window position & size
* Spout output settings
* OSC input settings

---

### OSC Control

Enable OSC input in settings.

* **Address**

  * `/9counter/play` → Play / Pause toggle
  * `/9counter/stop` → Stop / Reset

* **Port**

  * User configurable in settings

* **IP Address**

  * Displayed in settings for easy remote connection

Example:

```
192.168.0.10:8000
/9counter/play
```

---

### Spout Output

* Enable in settings
* Supports:

  * Custom resolution
  * Transparent background (Alpha)
  * Text outline rendering

---

## Notes

1. To use Spout output, you need an application that can receive Spout input (e.g., media server applications).
2. When using Spout on a system with both integrated and dedicated GPUs, make sure both the sender and receiver apps use the same GPU.  
   * Go to **Settings → System → Display → Graphics**, add **9Counter** as a desktop app and set it to **High Performance (dedicated GPU)**.  
   Apply the same setting to the receiving application (e.g., Resolume Arena, TouchDesigner).
3. If the output appears vertically flipped, enable the **Flip** option.

**Warning :**  
* If a dedicated GPU is present and the sender (9Counter) and receiver apps use different GPUs, the receiver application may crash or behave unexpectedly.
* During operation, moving or resizing the window may briefly pause the display.

---

## ✨ Tip

This app is a portable application (no installation required), so you can run multiple instances simultaneously and use them as independent counters with different timings.  
If you need multiple counters, copy the app into separate folders and run each instance with different **Spout output names** and **OSC ports**.

---
---

# 9Counter V1  

## 개요

9Counter는 시작시간/종료시간 설정이 가능한 카운트업 타이머 입니다.
밀리초 단위표시, Spout영상출력, OSC원격제어를 지원하며,
24시간 이상의 시간을 표기하는 옵션이 있습니다.

---

## 주요 기능

*  카운트업 타이머 (24시간 이상 표시 가능)
*  시작 / 종료 시간 설정
*  폰트, 색상, 외곽선 설정
*  테두리 제거 / 항상 위 표시
*  Spout 출력 (투명 배경 지원)
*  OSC 원격 제어 (Play / Stop)

---

## 사용 방법

### 기본 단축키

| 키        | 기능        |
| -------- | --------- |
| Space    | 재생 / 일시정지 |
| S        | 정지 / 리셋   |
| F        | 전체화면      |
| ESC      | 전체화면 해제   |
| F2       | 설정창       |
| T        | 항상 위      |
| B        | 테두리 제거    |
| Ctrl + Q | 종료        |

---

### 설정

**F2** 키로 설정창 진입

* 시작 / 종료 시간
* 밀리초 표시
* 24시간 이상 표시
* 폰트 / 색상 / 외곽선
* 창 위치 및 크기
* Spout 설정
* OSC 설정

---

### OSC 제어

설정에서 OSC 활성화

* **주소**

  * `/9counter/play` → 재생 / 일시정지
  * `/9counter/stop` → 정지 / 리셋

* **포트**

  * 설정에서 지정

* **IP**

  * 설정창에 표시됨

예시:

```
192.168.0.10:8000
/9counter/play
```

---

### Spout 출력

* 설정에서 활성화
* 지원 기능:

  * 해상도 설정
  * 투명 배경
  * 텍스트 외곽선

---

## 참고사항

1. Spout 출력을 사용하려면, Spout 입력을 받을 수 있는 앱(미디어서버 등)이 필요합니다.
2. 외장 그래픽카드가 있는 경우, Spout 송신/수신 앱의 그래픽카드를 동일하게 설정해야 합니다.  
   * **설정 → 시스템 → 디스플레이 → 그래픽**에서 9Counter를 데스크탑 앱으로 추가한 후 **고성능(외장 GPU)**으로 설정하세요.  
   Spout를 받는 앱(Resolume Arena, TouchDesigner 등)도 동일하게 외장 GPU로 설정해야 합니다.
3. 출력이 상하 반전되어 보일 경우, **Flip 옵션**을 체크하세요.

**주의 :**  
* 외장 그래픽카드가 있는 환경에서 9Counter와 Spout 수신 앱이 사용하는 GPU가 서로 다를 경우, 수신 앱이 비정상 종료되거나 오작동할 수 있습니다.
* 카운트 작동중 창 이동/리사이즈를 하면 화면이 잠깐 멈출 수 있습니다.

---

## ✨ 팁

이 앱은 설치형이 아닌 포터블 앱이어서 여러 개를 동시에 실행하여 각각 다른 시간의 카운터로 사용할 수 있습니다.  
여러 개의 카운터가 필요한 경우, 앱을 각각 다른 폴더에 복사하고 **Spout 출력 이름**과 **OSC 포트**를 서로 다르게 설정하여 사용하세요.  

