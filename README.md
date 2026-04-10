![Platform](https://img.shields.io/badge/platform-Windows-blue) [![Release](https://img.shields.io/badge/Release-V1.3-fc1ba6)](https://github.com/Yoons-B1/9Counter-V1/releases) ![License](https://img.shields.io/github/license/Yoons-B1/9Counter-V1)
# <img width="36" height="36" alt="9icon copy" src="https://github.com/user-attachments/assets/59fa5943-f3d1-48b7-9af0-5323b2ed6037" /> 9Counter V1

## ▶️ Overview

9Counter is a count-up timer with configurable start and end time.

It supports millisecond display, Spout video output, and OSC remote control.
It also includes an option to display time beyond 24 hours.

---

## ▶️ Features

*  Count-up timer (supports 24+ hours display)
*  Start / End time configuration
*  Font, color, and outline settings (Spout)
*  Borderless / Always-on-top mode
*  Spout output (with alpha transparency)
*  OSC remote control (Play / Stop)

---

## ▶️ Usage

### ⚙️ Basic Controls

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
---
<img width="671" height="645" alt="2026-04-10 13 09 18" src="https://github.com/user-attachments/assets/8f7679da-a40b-430c-94ec-7222a6ca732c" />  

### ⚙️ Settings

Press **F2** to open settings.

* Start Time / End Time
* Show milliseconds
* Continuous hours (24+)
* Font / Color / Outline
* Window position & size
* Spout output settings
* OSC input settings

---

### ⚙️ OSC Control

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

### ⚙️ Spout Output

* Enable in settings
* Supports:

  * Custom resolution
  * Transparent background (Alpha)
  * Text outline rendering

---

## ⚠️ Notes

* During operation, moving or resizing the window may briefly pause the display.

---
---

# 9카운터 V1  

## ▶️ 개요

9Counter는 시작시간/종료시간 설정이 가능한 카운트업 타이머 입니다.
밀리초 단위표시, Spout영상출력, OSC원격제어를 지원하며,
24시간 이상의 시간을 표기하는 옵션이 있습니다.

---

## ▶️ 주요 기능

*  카운트업 타이머 (24시간 이상 표시 가능)
*  시작 / 종료 시간 설정
*  폰트, 색상, 외곽선 설정
*  테두리 제거 / 항상 위 표시
*  Spout 출력 (투명 배경 지원)
*  OSC 원격 제어 (Play / Stop)

---

## ▶️ 사용 방법

### ⚙️ 기본 단축키

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

### ⚙️ 설정

**F2** 키로 설정창 진입

* 시작 / 종료 시간
* 밀리초 표시
* 24시간 이상 표시
* 폰트 / 색상 / 외곽선
* 창 위치 및 크기
* Spout 설정
* OSC 설정

---

### ⚙️ OSC 제어

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

### ⚙️ Spout 출력

* 설정에서 활성화
* 지원 기능:

  * 해상도 설정
  * 투명 배경
  * 텍스트 외곽선

---

## ⚠️ 참고사항

* 카운트 작동중 창 이동/리사이즈를 하면 화면이 잠깐 멈출 수 있음
