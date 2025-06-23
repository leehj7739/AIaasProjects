# OCR & GPT API

EasyOCR과 GPT를 연동한 텍스트 추출 및 책 제목 분석 API 서버입니다.

## 🚀 주요 기능

- **📸 OCR 텍스트 추출**: 이미지에서 텍스트 추출 (EasyOCR)
- **🤖 GPT 책 제목 분석**: 추출된 텍스트에서 책 제목 추출
- **🖼️ 박싱 이미지 생성**: 텍스트가 박스로 표시된 결과 이미지
- **⚡ 통합 API**: OCR + GPT 한 번에 처리
- **🔄 파일 관리**: 결과 이미지 자동 정리 (20개 유지)
- **🌐 React 연동**: 프론트엔드와 쉽게 연동

## 🛠️ 기술 스택

- **Backend**: FastAPI
- **OCR**: EasyOCR (한국어/영어 지원)
- **AI**: OpenAI GPT-3.5-turbo
- **이미지 처리**: OpenCV, Pillow
- **한글 폰트**: 맑은 고딕, 굴림 등 지원

## 📦 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 서버 설정
HOST=0.0.0.0
PORT=8000

# 보안 설정
SECRET_KEY=your-secret-key-here
```

### 3. 서버 실행

```bash
# 개발 모드
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API 엔드포인트

### 🎯 통합 OCR + GPT 엔드포인트

#### 파일 업로드 방식 (운영 모드)
```
POST /api/ocr/extract-and-analyze
```
- **file**: 이미지 파일 업로드
- **mode**: "prod" (기본값)
- **gpt_prompt**: "책 제목 추출" (기본값)

#### JSON 요청 방식 (테스트 모드)
```
POST /api/ocr/extract-and-analyze-test
```
```json
{
  "image_url": "test_image.jpg",
  "mode": "test",
  "gpt_prompt": "책 제목 추출"
}
```

### 📸 OCR 관련

- `POST /api/ocr/extract`: 이미지에서 텍스트 추출
- `POST /api/ocr/batch-extract`: 여러 이미지 일괄 처리
- `GET /api/ocr/result/{filename}`: 결과 이미지 다운로드

### 🤖 GPT 관련

- `POST /api/gpt/analyze`: 텍스트 분석
- `POST /api/gpt/extract-book-title`: 책 제목 추출
- `POST /api/gpt/summarize`: 텍스트 요약
- `POST /api/gpt/translate`: 텍스트 번역

### 🏥 헬스체크

- `GET /api/health`: 서버 상태 확인

## 📝 사용 예시

### React에서 통합 API 사용

```javascript
// React에서 파일 업로드 후 API 호출
const handleImageUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', 'prod');
  formData.append('gpt_prompt', '책 제목 추출');

  const response = await fetch('http://localhost:8000/api/ocr/extract-and-analyze', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  
  // 결과 사용
  console.log('추출된 텍스트:', result.ocr_result.extracted_text);
  console.log('책 제목:', result.gpt_result.gpt_response);
  console.log('박싱 이미지:', result.ocr_result.result_image_url);
};
```

### Python에서 API 호출

```python
import requests

# 파일 업로드 방식
with open('book_cover.jpg', 'rb') as f:
    files = {'file': f}
    data = {'mode': 'prod', 'gpt_prompt': '책 제목 추출'}
    response = requests.post('http://localhost:8000/api/ocr/extract-and-analyze', 
                           files=files, data=data)

result = response.json()
print(f"추출된 텍스트: {result['ocr_result']['extracted_text']}")
print(f"책 제목: {result['gpt_result']['gpt_response']}")
print(f"박싱 이미지: {result['ocr_result']['result_image_url']}")
```

## 📁 프로젝트 구조

```
back_fastapi/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config/
│   │   └── settings.py         # 환경변수, 설정 관리
│   ├── api/
│   │   └── routes/
│   │       ├── ocr.py         # OCR 관련 엔드포인트
│   │       ├── gpt.py         # GPT 관련 엔드포인트
│   │       └── health.py      # 헬스체크 엔드포인트
│   ├── core/
│   │   ├── security.py        # CORS, 인증 등 보안 설정
│   │   └── exceptions.py      # 커스텀 예외 처리
│   ├── services/
│   │   ├── ocr_service.py     # EasyOCR 서비스 로직
│   │   ├── gpt_service.py     # GPT API 서비스 로직
│   │   └── image_service.py   # 이미지 처리 서비스
│   ├── models/
│   │   ├── request.py         # 요청 모델 (Pydantic)
│   │   └── response.py        # 응답 모델 (Pydantic)
│   └── static/
│       ├── uploads/           # 업로드된 이미지 저장
│       └── results/           # 처리된 결과 이미지 저장 (20개 유지)
├── requirements.txt           # Python 의존성
├── .env                      # 환경변수 (API 키 등)
├── .gitignore               # Git 무시 파일
└── README.md
```

## 🔧 주요 특징

### 🎯 OCR 기능
- **다중 언어 지원**: 한국어, 영어
- **이미지 전처리**: 노이즈 제거, 대비 향상
- **다중 스케일 처리**: 작은 텍스트도 포착
- **신뢰도 기반 필터링**: 낮은 신뢰도 결과 제거

### 🤖 GPT 기능
- **책 제목 추출**: OCR 결과에서 책 제목 분석
- **한글 최적화**: 한국어 텍스트 처리에 특화
- **프롬프트 엔지니어링**: 정확한 추출을 위한 전문 프롬프트

### 🖼️ 이미지 처리
- **박싱 이미지**: 텍스트가 박스로 표시된 결과 이미지
- **한글 폰트**: 맑은 고딕, 굴림 등 지원
- **자동 정리**: 결과 이미지 20개 유지

## 🖼️ 이미지 저장 정책

### 현재 설정 (권장)

```python
# app/config/settings.py
SAVE_UPLOADED_IMAGES: bool = False  # 업로드된 원본 이미지 저장 안함
SAVE_RESULT_IMAGES: bool = False    # OCR 결과 이미지 저장 안함
CLEANUP_OLD_IMAGES: bool = True     # 오래된 이미지 자동 정리
IMAGE_RETENTION_HOURS: int = 24     # 이미지 보관 시간 (24시간)
```

### 이미지 저장 비활성화 이유

1. **🔒 보안 및 개인정보 보호**
   - 사용자 업로드 이미지의 개인정보 유출 방지
   - GDPR, 개인정보보호법 준수

2. **💾 저장공간 최적화**
   - 디스크 공간 절약
   - 서버 성능 향상

3. **⚡ 성능 최적화**
   - 파일 I/O 작업 최소화
   - 메모리 사용량 감소

### 이미지 저장 활성화 방법

개발/디버깅 목적으로 이미지 저장이 필요한 경우:

```python
# app/config/settings.py에서 설정 변경
SAVE_UPLOADED_IMAGES: bool = True   # 원본 이미지 저장
SAVE_RESULT_IMAGES: bool = True     # 결과 이미지 저장
```

### 이미지 정리

```bash
# 수동 정리 스크립트 실행
python cleanup_images.py

# API를 통한 정리
curl -X DELETE http://localhost:8000/api/ocr/results/cleanup

# 개별 이미지 삭제
curl -X DELETE http://localhost:8000/api/ocr/result/{filename}
```

## ⚠️ 주의사항

1. **API 키 보안**: `.env` 파일에 API 키를 저장하고, 절대 Git에 커밋하지 마세요.
2. **파일 크기 제한**: 기본적으로 10MB까지 업로드 가능합니다.
3. **지원 이미지 형식**: JPG, JPEG, PNG, BMP, TIFF
4. **OCR 언어**: 한국어(ko), 영어(en) 지원
5. **결과 이미지**: 20개 초과 시 자동으로 오래된 파일 삭제

## 🚀 React 연동

이 API는 React 프론트엔드와 쉽게 연동할 수 있도록 설계되었습니다:

1. **CORS 설정**: React 개발 서버 (localhost:3000) 허용
2. **파일 업로드**: FormData를 사용한 이미지 업로드
3. **결과 표시**: 추출된 텍스트, 책 제목, 박싱 이미지 반환

## 📄 라이선스

MIT License

## 🤝 기여

이슈나 풀 리퀘스트를 통해 기여해주세요. 