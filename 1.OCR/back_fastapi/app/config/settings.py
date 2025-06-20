"""
애플리케이션 설정 관리 모듈

이 파일은 OCR & GPT API 서버의 모든 설정값을 중앙에서 관리합니다.
환경변수(.env 파일)에서 설정을 로드하고, 기본값을 제공합니다.

주요 설정 카테고리:
- API 및 서버 설정
- CORS 설정 (프론트엔드 연동용)
- OpenAI API 설정
- EasyOCR 설정
- 파일 업로드 설정
- 보안 설정
"""

import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
# .env 파일이 없어도 오류가 발생하지 않음
load_dotenv()

class Settings:
    """
    애플리케이션 설정 클래스
    
    모든 설정값을 클래스 변수로 정의하여 중앙 집중식으로 관리
    환경변수가 있으면 환경변수 사용, 없으면 기본값 사용
    """
    
    # ==================== API 설정 ====================
    API_V1_STR: str = "/api"                    # API 버전 경로
    PROJECT_NAME: str = "OCR & GPT API"         # 프로젝트 이름 (Swagger UI에 표시)
    
    # ==================== 서버 설정 ====================
    HOST: str = os.getenv("HOST", "0.0.0.0")    # 서버 호스트 (0.0.0.0 = 모든 IP 허용)
    PORT: int = int(os.getenv("PORT", "8000"))  # 서버 포트
    
    # ==================== CORS 설정 ====================
    # Cross-Origin Resource Sharing 설정
    # React 등 프론트엔드에서 API 호출을 허용하기 위한 설정
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:3001",  # React 대체 포트
        "http://127.0.0.1:3000",  # React localhost
        "http://127.0.0.1:3001",  # React 대체 포트
        "http://192.168.45.120:3000",  # React 서버 (네트워크 IP)
    ]
    
    # ==================== OpenAI 설정 ====================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # OpenAI API 키 (.env에서 로드)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # 사용할 GPT 모델
    
    # ==================== EasyOCR 설정 ====================
    OCR_LANGUAGES: list = ["ko", "en"]  # OCR에서 인식할 언어 (한국어, 영어)
    
    # ==================== 파일 업로드 설정 ====================
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 최대 파일 크기 (10MB)
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]  # 허용된 이미지 형식
    UPLOAD_DIR: str = "app/static/uploads"   # 업로드된 파일 저장 경로
    RESULTS_DIR: str = "app/static/results"  # OCR 결과 이미지 저장 경로
    
    # ==================== 보안 설정 ====================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")  # JWT 토큰 암호화 키
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 액세스 토큰 만료 시간 (8일)

# 전역 설정 인스턴스 생성
# 다른 모듈에서 from app.config.settings import settings로 사용
settings = Settings() 