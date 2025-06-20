from pydantic import BaseModel, Field
from typing import Optional, List

class OCRRequest(BaseModel):
    """OCR 요청 모델"""
    image_url: Optional[str] = Field(None, description="이미지 URL")
    enhance_image: bool = Field(True, description="이미지 품질 향상 여부")
    languages: List[str] = Field(["ko", "en"], description="인식할 언어 목록")

class GPTRequest(BaseModel):
    """GPT 요청 모델"""
    text: str = Field(..., description="분석할 텍스트", min_length=1)
    prompt: str = Field("", description="GPT에게 전달할 프롬프트")
    max_tokens: int = Field(1000, description="최대 토큰 수", ge=1, le=4000)
    temperature: float = Field(0.7, description="창의성 수준", ge=0.0, le=2.0)

class BatchOCRRequest(BaseModel):
    """배치 OCR 요청 모델"""
    image_urls: List[str] = Field(..., description="이미지 URL 목록")
    enhance_image: bool = Field(True, description="이미지 품질 향상 여부")

class BatchGPTRequest(BaseModel):
    """배치 GPT 요청 모델"""
    texts: List[str] = Field(..., description="분석할 텍스트 목록")
    prompt: str = Field("", description="GPT에게 전달할 프롬프트")

class CombinedRequest(BaseModel):
    """OCR + GPT 통합 요청 모델"""
    image_url: Optional[str] = Field(None, description="이미지 URL")
    gpt_prompt: str = Field("", description="추출된 텍스트에 대한 GPT 프롬프트")
    enhance_image: bool = Field(True, description="이미지 품질 향상 여부")
    mode: str = Field("prod", description="실행 모드(test: 더미/테스트 이미지, prod: 업로드 이미지)") 