# OCR & GPT API 프로젝트 구조 및 기능 분석

## 📋 프로젝트 개요

이 프로젝트는 FastAPI 기반의 OCR(Optical Character Recognition)과 GPT를 연동한 텍스트 추출 및 책 제목 분석 API 서버입니다.

### 🎯 핵심 기능
1. **이미지에서 텍스트 추출** (EasyOCR)
2. **추출된 텍스트에서 책 제목 분석** (GPT)
3. **박싱 이미지 생성** (텍스트 박스 표시)
4. **통합 API 제공** (OCR + GPT 한 번에 처리)

## 🏗️ 아키텍처 패턴

### 레이어드 아키텍처
```
┌─────────────────────────────────────┐
│           API Layer                 │  ← FastAPI 라우터
├─────────────────────────────────────┤
│         Service Layer               │  ← 비즈니스 로직
├─────────────────────────────────────┤
│         Model Layer                 │  ← Pydantic 모델
├─────────────────────────────────────┤
│         Config Layer                │  ← 설정 관리
└─────────────────────────────────────┘
```

### 데이터 플로우
```
이미지 업로드 → OCR 서비스 → 텍스트 추출 → GPT 서비스 → 책 제목 분석 → 결과 반환
```

## 📁 프로젝트 구조 상세 분석

### 1. `app/main.py` - 애플리케이션 진입점
```python
# 주요 역할:
- FastAPI 앱 인스턴스 생성
- CORS 미들웨어 설정 (React 연동용)
- 정적 파일 서빙 설정 (결과 이미지 제공)
- API 라우터 등록 (OCR, GPT, 헬스체크)
```

### 2. `app/config/settings.py` - 설정 관리
```python
# 주요 설정 카테고리:
- API 및 서버 설정 (HOST, PORT)
- CORS 설정 (프론트엔드 연동용)
- OpenAI API 설정 (API 키, 모델)
- EasyOCR 설정 (언어 설정)
- 파일 업로드 설정 (크기 제한, 허용 형식)
- 보안 설정 (JWT 토큰 등)
```

### 3. `app/api/routes/` - API 엔드포인트

#### `ocr.py` - OCR 관련 API
```python
# 주요 엔드포인트:
- POST /api/ocr/extract: 기본 OCR 텍스트 추출
- POST /api/ocr/extract-and-analyze: 통합 OCR+GPT (파일 업로드)
- POST /api/ocr/extract-and-analyze-test: 통합 OCR+GPT (JSON 요청)
- POST /api/ocr/batch-extract: 배치 OCR 처리
- GET /api/ocr/result/{filename}: 결과 이미지 다운로드
```

#### `gpt.py` - GPT 관련 API
```python
# 주요 엔드포인트:
- POST /api/gpt/analyze: 일반 텍스트 분석
- POST /api/gpt/extract-book-title: 책 제목 추출
- POST /api/gpt/summarize: 텍스트 요약
- POST /api/gpt/translate: 텍스트 번역
```

#### `health.py` - 헬스체크 API
```python
# 주요 엔드포인트:
- GET /api/health: 서버 상태 확인
```

### 4. `app/services/` - 비즈니스 로직

#### `ocr_service.py` - OCR 서비스
```python
# 주요 기능:
class OCRService:
    def __init__(self):
        # EasyOCR 리더 초기화 (한국어, 영어 지원)
    
    def _preprocess_image(self, image):
        # 이미지 전처리 (노이즈 제거, 대비 향상, 이진화)
    
    def _preprocess_multiscale(self, image):
        # 다중 스케일 전처리 (작은 텍스트 포착)
    
    def _enhance_small_text(self, image):
        # 작은 텍스트 강화 전처리
    
    def _resize_image(self, image):
        # 이미지 크기 조정 (처리 속도 향상)
    
    def _filter_and_merge_results(self, all_results):
        # OCR 결과 필터링 및 중복 제거
    
    def _create_result_image(self, image, results):
        # 박싱 이미지 생성 (텍스트 박스 표시)
    
    async def extract_text(self, file):
        # 파일 업로드 기반 OCR
    
    async def extract_text_from_path(self, image_path):
        # 파일 경로 기반 OCR
    
    async def extract_text_with_mode(self, file, image_path, mode):
        # 모드에 따른 OCR (운영/테스트)
```

#### `gpt_service.py` - GPT 서비스
```python
# 주요 기능:
class GPTService:
    def __init__(self):
        # OpenAI 클라이언트 초기화
    
    async def analyze_text(self, text, prompt):
        # 일반 텍스트 분석
    
    async def extract_book_title(self, text):
        # 책 제목 추출 (전문 프롬프트 사용)
    
    async def summarize_text(self, text):
        # 텍스트 요약
    
    async def translate_text(self, text):
        # 텍스트 번역
```

### 5. `app/models/` - 데이터 모델

#### `request.py` - 요청 모델
```python
# 주요 모델:
- OCRRequest: OCR 요청 모델
- GPTRequest: GPT 요청 모델
- CombinedRequest: 통합 요청 모델 (mode 파라미터 포함)
```

#### `response.py` - 응답 모델
```python
# 주요 모델:
- OCRResponse: OCR 응답 모델
- GPTResponse: GPT 응답 모델
- CombinedResponse: 통합 응답 모델
- HealthResponse: 헬스체크 응답 모델
```

### 6. `app/core/` - 핵심 기능

#### `exceptions.py` - 커스텀 예외
```python
# 주요 예외:
- OCRException: OCR 관련 예외
- GPTException: GPT 관련 예외
```

#### `security.py` - 보안 설정
```python
# 주요 기능:
- setup_cors(): CORS 설정
- CORS 미들웨어 구성
```

### 7. `app/static/` - 정적 파일
```
app/static/
├── uploads/     # 업로드된 이미지 저장
└── results/     # OCR 결과 이미지 저장 (20개 유지)
```

## 🔧 주요 기술적 특징

### 1. 이미지 전처리 기법
```python
# 적용되는 전처리 기법:
1. 그레이스케일 변환
2. 노이즈 제거 (가우시안 블러)
3. 대비 향상 (CLAHE)
4. 샤프닝 필터
5. 모폴로지 연산
6. 적응형 이진화
7. 다중 스케일 처리
```

### 2. OCR 최적화
```python
# 성능 최적화 기법:
- 이미지 크기 조정 (1024px 기준)
- 신뢰도 기반 필터링 (0.1 이상)
- 중복 텍스트 제거
- 다중 전처리 방법 시도
```

### 3. GPT 프롬프트 엔지니어링
```python
# 책 제목 추출을 위한 전문 프롬프트:
- 핵심 키워드 우선
- 길이 고려 (2-8단어)
- 언어 우선순위 (한글 > 영어)
- 노이즈 제거
- 문맥 분석
```

### 4. 파일 관리
```python
# 자동 파일 정리:
- 결과 이미지 20개 유지
- 오래된 파일 자동 삭제
- UUID 기반 파일명 생성
```

## 🔄 API 호출 플로우

### 1. 통합 API 호출 (운영 모드)
```javascript
// React에서 사용 예시
const formData = new FormData();
formData.append('file', imageFile);
formData.append('mode', 'prod');
formData.append('gpt_prompt', '책 제목 추출');

const response = await fetch('/api/ocr/extract-and-analyze', {
    method: 'POST',
    body: formData
});
```

### 2. 응답 구조
```json
{
  "ocr_result": {
    "original_filename": "image.jpg",
    "extracted_text": "추출된 텍스트",
    "confidence_scores": [0.95, 0.87],
    "bounding_boxes": [[[x1,y1],[x2,y2]]],
    "result_image_url": "/static/results/uuid.jpg",
    "total_text_count": 2,
    "processing_time_ms": 1500
  },
  "gpt_result": {
    "original_text": "추출된 텍스트",
    "prompt": "책 제목 추출",
    "gpt_response": "추정: 책 제목",
    "gpt_model": "gpt-3.5-turbo",
    "tokens_used": 150,
    "response_time_ms": 800
  },
  "total_processing_time_ms": 2300
}
```

## 🚀 리팩토링 및 개선 방향

### 1. 코드 구조 개선
- [ ] 각 메서드에 상세한 docstring 추가
- [ ] 타입 힌트 완성
- [ ] 에러 처리 강화
- [ ] 로깅 시스템 구축

### 2. 성능 최적화
- [ ] 비동기 처리 최적화
- [ ] 캐싱 시스템 도입
- [ ] 배치 처리 개선
- [ ] 메모리 사용량 최적화

### 3. 기능 확장
- [ ] 더 많은 언어 지원
- [ ] 다양한 이미지 형식 지원
- [ ] 고급 이미지 전처리 옵션
- [ ] 사용자 정의 프롬프트 지원

### 4. 테스트 및 문서화
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] API 문서 개선
- [ ] 사용 예시 추가

## 📚 학습 포인트

### 1. FastAPI 패턴
- 라우터 분리 및 모듈화
- Pydantic 모델을 통한 데이터 검증
- 비동기 처리
- 미들웨어 활용

### 2. 이미지 처리
- OpenCV 활용
- 다양한 전처리 기법
- 성능 최적화
- 한글 폰트 처리

### 3. AI 서비스 연동
- OpenAI API 활용
- 프롬프트 엔지니어링
- 비동기 API 호출
- 에러 처리

### 4. 파일 관리
- 정적 파일 서빙
- 파일 업로드 처리
- 자동 정리 시스템
- 보안 고려사항

이 문서를 참고하여 코드를 이해하고 리팩토링하시면 됩니다! 