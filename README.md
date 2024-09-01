# Posture Guard

**거북목과 일자목의 지속적인 모니터링을 통한 척추 및 목 건강 지킴이**

사용자의 카메라를 활용한 실시간/일간/주간 자세 분석 및 기록 데스크탑 앱

## Overview

https://github.com/user-attachments/assets/cfb2e5e5-910f-43f9-8625-2170290d006a

1. 영상 하단에 실시간 IP 카메라 주소를 입력하여 열람실 카메라 실시간 송출
2. 9번 좌석 : 사석화 자리에 대해 일정 시간 지난 후, 자동으로 좌석 반납 처리
3. 10번 좌석 : 잠시 자리를 비운 경우는 사석화와 달리 좌석 반납 처리가 되지 않음
4. 3번 좌석 : 자리를 떠났지만 시스템 상 반납을 깜박한 경우, 일정 시간 지난 후 자동으로 좌석 반납 처리

**네트워크 포트포워딩을 통해 송출한 실시간 IP카메라의 영상을 서버에서 프레임 단위로 받아 자체 구축한 YOLOv5 모델로 분석 후 결과값을 DB에 쌓아 상황에 따라 알맞은 처리를 진행합니다.**

## Project Architecture

<img src="https://github.com/LibraryDetection/.github/assets/79658037/e751cdd9-2e55-4651-8c4d-d7c2277488e1" align="center" style="width:50rem; height:auto;"></img>
