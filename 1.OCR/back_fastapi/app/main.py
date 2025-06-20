"""
FastAPI 메인 애플리케이션 진입점

이 파일은 OCR & GPT API 서버의 메인 애플리케이션을 정의합니다.
FastAPI 인스턴스를 생성하고, 미들웨어, 라우터, 정적 파일 서빙을 설정합니다.

주요 기능:
- FastAPI 앱 초기화 및 설정
- CORS 미들웨어 설정 (React 등 프론트엔드 연동용)
- 정적 파일 서빙 설정 (결과 이미지 제공용)
- API 라우터 등록 (OCR, GPT, 헬스체크)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import ocr, gpt, health
from app.core.security import setup_cors

# FastAPI 애플리케이션 인스턴스 생성
# title, description, version은 Swagger UI에서 표시됩니다
app = FastAPI(
    title="OCR & GPT API",
    description="EasyOCR과 GPT를 연동한 텍스트 추출 및 분석 API",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing) 설정
# React 등 프론트엔드에서 API 호출을 허용하기 위한 설정
setup_cors(app)

# 정적 파일 서빙 설정
# app/static 폴더의 파일들을 /static 경로로 제공
# OCR 결과 이미지 등을 웹에서 접근할 수 있게 함
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API 라우터 등록
# 각 기능별로 라우터를 분리하여 관리
app.include_router(health.router, prefix="/api", tags=["health"])  # 헬스체크 API
app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])    # OCR 관련 API
app.include_router(gpt.router, prefix="/api/gpt", tags=["gpt"])    # GPT 관련 API

@app.get("/")
async def root():
    """
    루트 엔드포인트
    
    서버가 정상적으로 실행 중인지 확인하는 간단한 엔드포인트
    """
    return {"message": "OCR & GPT API 서버가 실행 중입니다."}

# 개발 환경에서 직접 실행할 때 사용
if __name__ == "__main__":
    import uvicorn
    # uvicorn을 사용하여 FastAPI 앱 실행
    # host="0.0.0.0": 모든 IP에서 접근 가능
    # port=8000: 8000번 포트에서 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8000) 