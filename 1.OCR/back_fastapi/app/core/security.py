from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

def setup_cors(app: FastAPI):
    """CORS 미들웨어 설정"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메서드 허용
        allow_headers=["*"],  # 모든 헤더 허용
    ) 