# 🎬 영화 추천 챗봇 (모듈화 버전)

Neo4j 그래프 데이터베이스와 RAG(Retrieval-Augmented Generation)를 활용한 영화 추천 시스템의 모듈화된 버전입니다.

## 📁 프로젝트 구조

```
sample/
├── config/                 # 설정 관리
│   ├── __init__.py
│   ├── constants.py        # 상수 정의
│   └── settings.py         # 환경변수 및 설정
├── core/                   # 핵심 기능
│   ├── __init__.py
│   ├── token_manager.py    # 토큰 관리
│   └── schema_manager.py   # 스키마 관리
├── models/                 # 데이터 모델
│   ├── __init__.py
│   └── chatbot.py         # 메인 챗봇 클래스
├── services/              # 비즈니스 로직
│   ├── __init__.py
│   ├── intent_classifier.py # 의도 분류
│   ├── cypher_generator.py  # Cypher 쿼리 생성
│   ├── response_generator.py # 응답 생성
│   └── database_service.py  # 데이터베이스 서비스
├── utils/                  # 유틸리티
│   ├── __init__.py
│   ├── data_utils.py       # 데이터 타입 유틸리티
│   └── format_utils.py     # 포맷팅 유틸리티
├── interface/              # 사용자 인터페이스
│   ├── __init__.py
│   ├── gradio_interface.py # Gradio 인터페이스
│   └── handlers.py         # 이벤트 핸들러
├── main.py                 # 메인 실행 파일
├── requirements.txt        # 의존성 목록
└── README.md              # 프로젝트 설명
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Neo4j 설정
NEO4J_URI=neo4j://54.152.35.230:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=designations-oscillations-convention

# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0

# 스키마 설정
SCHEMA_FILE_PATH=guide/movie_schema.json

# 토큰 제한 설정
MAX_TOKENS_PER_REQUEST=4000
MAX_TOKENS_PER_DAY=50000
MAX_CONVERSATION_LENGTH=20

# Gradio 서버 설정
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
```

### 3. 실행

```bash
python main.py
```

## 🔧 주요 기능

### 1. 모듈화된 구조
- **설정 관리**: 환경변수와 상수를 체계적으로 관리
- **핵심 기능**: 토큰 관리, 스키마 관리 등 핵심 기능 분리
- **서비스 레이어**: 의도 분류, 쿼리 생성, 응답 생성 등 비즈니스 로직 분리
- **유틸리티**: 데이터 타입 변환, 포맷팅 등 재사용 가능한 함수들
- **인터페이스**: Gradio UI와 이벤트 핸들러 분리

### 2. 의도 분류 시스템
- 사용자 질문을 자동으로 영화 관련/일반 대화로 분류
- 분류 결과에 따라 적절한 처리 로직 적용

### 3. Cypher 쿼리 자동 생성
- 자연어를 Neo4j Cypher 쿼리로 변환
- 스키마 기반 예시 생성 및 학습
- 한국어-영어 키워드 자동 번역

### 4. 토큰 관리
- OpenAI API 토큰 사용량 추적
- 일일/요청당 토큰 제한
- 자동 일일 제한 초기화

### 5. 스키마 관리
- Neo4j 데이터베이스 스키마 자동 추출
- 스키마 파일 캐싱으로 성능 향상
- 스키마 기반 예시 쿼리 생성

## 📊 모듈별 역할

### config/
- **constants.py**: 시스템 상수 정의
- **settings.py**: 환경변수 로드 및 설정 관리

### core/
- **token_manager.py**: OpenAI API 토큰 사용량 관리
- **schema_manager.py**: Neo4j 스키마 로드, 캐싱, 포맷팅

### models/
- **chatbot.py**: 메인 GraphRAGChatbot 클래스

### services/
- **intent_classifier.py**: 사용자 의도 분류
- **cypher_generator.py**: 자연어를 Cypher 쿼리로 변환
- **response_generator.py**: 검색 결과를 자연스러운 응답으로 생성
- **database_service.py**: Neo4j 연결 및 쿼리 실행

### utils/
- **data_utils.py**: 데이터 타입 변환, 예시 생성
- **format_utils.py**: 스키마, 결과 등 포맷팅

### interface/
- **gradio_interface.py**: Gradio 웹 인터페이스 구성
- **handlers.py**: 이벤트 핸들러 함수들

## 🎯 사용 예시

### 영화 관련 질문
- "Tom Hanks가 출연한 영화는?"
- "액션 영화 추천해줘"
- "The Matrix와 비슷한 영화는?"
- "로맨스 영화 중에서 평점이 높은 것들은?"

### 일반 대화
- "안녕하세요"
- "내 이름은 홍길동이야"
- "너는 누구야?"
- "잘 지내?"

## 🔍 주요 개선사항

### 1. 코드 구조 개선
- 단일 책임 원칙 적용
- 모듈간 의존성 최소화
- 재사용 가능한 컴포넌트 분리

### 2. 유지보수성 향상
- 기능별 모듈 분리로 수정 용이성 증가
- 명확한 인터페이스 정의
- 테스트 가능한 구조

### 3. 확장성 개선
- 새로운 기능 추가 시 적절한 모듈에 추가
- 설정 변경 시 config 모듈만 수정
- 새로운 서비스 추가 시 services 모듈 확장

### 4. 가독성 향상
- 각 파일의 역할이 명확
- 함수와 클래스의 책임 분리
- 일관된 코딩 스타일

## 🛠️ 개발 가이드

### 새로운 기능 추가
1. 기능의 성격에 따라 적절한 모듈 선택
2. 기존 인터페이스와 호환성 유지
3. 설정이 필요한 경우 config 모듈에 추가
4. 테스트 코드 작성

### 설정 변경
1. `config/constants.py`에서 상수 수정
2. `config/settings.py`에서 환경변수 추가
3. `.env` 파일에 해당 환경변수 추가

### 새로운 서비스 추가
1. `services/` 디렉토리에 새 서비스 클래스 생성
2. `models/chatbot.py`에서 서비스 통합
3. 필요한 경우 `interface/handlers.py`에 핸들러 추가

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다! 