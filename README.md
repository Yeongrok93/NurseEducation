# NurseEducation

SBAR 기반 의사소통 훈련을 위한 간호 교육용 웹 시뮬레이션 프로젝트입니다.  
간호사가 중환자실 상황에서 의사에게 보고하는 흐름을 연습하고, 입력한 메시지를 SBAR 기준으로 평가하며, 의사 응답을 시뮬레이션합니다.

## Overview

- `Flask` 기반 웹 애플리케이션
- 시나리오 데이터는 `JSON`으로 관리
- `OpenAI API`를 사용해 SBAR 평가와 의사 응답 생성 수행
- 환자 모니터, 차트, 검사 결과를 포함한 단일 화면형 시뮬레이션 UI 제공

## Project Structure

- `app.py`: Flask 서버 진입점 및 API 라우팅
- `engine/`: 게임 상태, 시나리오 로딩, 평가기, 의사 에이전트 로직
- `scenarios/`: 시뮬레이션 시나리오 데이터
- `templates/`: 화면 템플릿
- `static/`: 이미지 등 정적 리소스

## Main Features

- SBAR 형식 자유 입력
- 환자 상태 모니터링
- 인공호흡기 및 검사 결과 조회
- 환자 차트 기반 상황 파악
- SBAR 항목별 피드백과 누적 점수 제공
- 턴 기반 진행 및 종료 조건 처리

## Requirements

- Python 3.10+
- OpenAI API Key

## Setup

1. 의존성 설치

```bash
pip install -r requirements.txt
```

2. 루트에 `.env` 파일 생성

```env
OPENAI_API_KEY=your_api_key
SECRET_KEY=your_secret_key
```

3. 서버 실행

```bash
python app.py
```

4. 브라우저에서 접속

```text
http://127.0.0.1:5000
```

## Notes

- 연구 자료 폴더와 개인 실험용 노트북은 Git 추적 대상에서 제외합니다.
- 세션 상태는 현재 메모리에 저장되므로 서버 재시작 시 초기화됩니다.
