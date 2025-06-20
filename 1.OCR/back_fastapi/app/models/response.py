from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class OCRResponse(BaseModel):
    """OCR 응답 모델"""
    original_filename: str = Field(..., description="원본 파일명")
    extracted_text: str = Field(..., description="추출된 텍스트")
    confidence_scores: List[float] = Field(..., description="신뢰도 점수 목록")
    bounding_boxes: List[List] = Field(..., description="바운딩 박스 좌표")
    result_image_url: str = Field(..., description="결과 이미지 URL")
    total_text_count: int = Field(..., description="추출된 텍스트 개수")
    processing_time_ms: Optional[float] = Field(None, description="처리 시간 (밀리초)")
    error_message: Optional[str] = Field(None, description="오류 메시지")

class GPTResponse(BaseModel):
    """GPT 응답 모델"""
    original_text: str = Field(..., description="원본 텍스트")
    prompt: str = Field(..., description="사용된 프롬프트")
    gpt_response: str = Field(..., description="GPT 응답")
    gpt_model: str = Field(..., description="사용된 모델")
    tokens_used: int = Field(..., description="사용된 토큰 수")
    response_time_ms: float = Field(..., description="응답 시간 (밀리초)")
    error_message: Optional[str] = Field(None, description="오류 메시지")

class CombinedResponse(BaseModel):
    """OCR + GPT 통합 응답 모델"""
    ocr_result: OCRResponse = Field(..., description="OCR 결과")
    gpt_result: GPTResponse = Field(..., description="GPT 결과")
    total_processing_time_ms: float = Field(..., description="총 처리 시간")

class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str = Field(..., description="서버 상태")
    message: str = Field(..., description="상태 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    version: str = Field("1.0.0", description="API 버전")

class ErrorResponse(BaseModel):
    """오류 응답 모델"""
    error: str = Field(..., description="오류 타입")
    message: str = Field(..., description="오류 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="오류 발생 시간")
    details: Optional[Any] = Field(None, description="상세 오류 정보")

class BatchOCRResponse(BaseModel):
    """배치 OCR 응답 모델"""
    results: List[OCRResponse] = Field(..., description="OCR 결과 목록")
    total_files: int = Field(..., description="총 파일 수")
    successful_files: int = Field(..., description="성공한 파일 수")
    failed_files: int = Field(..., description="실패한 파일 수")

class BatchGPTResponse(BaseModel):
    """배치 GPT 응답 모델"""
    results: List[GPTResponse] = Field(..., description="GPT 결과 목록")
    total_texts: int = Field(..., description="총 텍스트 수")
    successful_texts: int = Field(..., description="성공한 텍스트 수")
    failed_texts: int = Field(..., description="실패한 텍스트 수") 