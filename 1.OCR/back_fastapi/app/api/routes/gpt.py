from fastapi import APIRouter, HTTPException
from typing import List

from app.services.gpt_service import GPTService
from app.models.request import GPTRequest
from app.models.response import GPTResponse
from app.config.settings import settings

router = APIRouter()
gpt_service = GPTService()

@router.post("/analyze", response_model=GPTResponse)
async def analyze_text(request: GPTRequest):
    """텍스트 분석 및 GPT 응답"""
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API 키가 설정되지 않았습니다."
            )
        
        # 책 제목 추출 요청인지 확인
        if request.prompt and "책 제목 추출" in request.prompt:
            result = await gpt_service.extract_book_title(request.text)
        else:
            result = await gpt_service.analyze_text(request.text, request.prompt)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/extract-book-title", response_model=GPTResponse)
async def extract_book_title(request: GPTRequest):
    """책 제목 추출 전용 엔드포인트"""
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API 키가 설정되지 않았습니다."
            )
        
        result = await gpt_service.extract_book_title(request.text)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"책 제목 추출 중 오류가 발생했습니다: {str(e)}")

@router.post("/summarize", response_model=GPTResponse)
async def summarize_text(request: GPTRequest):
    """텍스트 요약"""
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API 키가 설정되지 않았습니다."
            )
        
        prompt = "다음 텍스트를 간결하게 요약해주세요:"
        result = await gpt_service.analyze_text(request.text, prompt)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"텍스트 요약 중 오류가 발생했습니다: {str(e)}")

@router.post("/translate", response_model=GPTResponse)
async def translate_text(request: GPTRequest):
    """텍스트 번역"""
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API 키가 설정되지 않았습니다."
            )
        
        prompt = "다음 텍스트를 한국어로 번역해주세요:"
        result = await gpt_service.analyze_text(request.text, prompt)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"텍스트 번역 중 오류가 발생했습니다: {str(e)}")

@router.post("/batch-analyze", response_model=List[GPTResponse])
async def batch_analyze_texts(requests: List[GPTRequest]):
    """여러 텍스트 일괄 분석"""
    try:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API 키가 설정되지 않았습니다."
            )
        
        results = []
        for request in requests:
            result = await gpt_service.analyze_text(request.text, request.prompt)
            results.append(result)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 분석 중 오류가 발생했습니다: {str(e)}") 