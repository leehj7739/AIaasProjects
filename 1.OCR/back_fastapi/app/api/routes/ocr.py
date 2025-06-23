from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
from typing import List

from app.services.ocr_service import OCRService
from app.models.request import OCRRequest, CombinedRequest
from app.models.response import OCRResponse, CombinedResponse
from app.config.settings import settings
from app.services.gpt_service import GPTService

router = APIRouter()
ocr_service = OCRService()
gpt_service = GPTService()

@router.post("/extract", response_model=OCRResponse)
async def extract_text_from_image(file: UploadFile = File(...)):
    """이미지에서 텍스트 추출"""
    try:
        # 파일 확장자 검증
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # 파일 크기 검증
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # OCR 처리
        result = await ocr_service.extract_text(file)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/batch-extract", response_model=List[OCRResponse])
async def extract_text_from_multiple_images(files: List[UploadFile] = File(...)):
    """여러 이미지에서 텍스트 추출"""
    try:
        results = []
        for file in files:
            # 파일 검증
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in settings.ALLOWED_EXTENSIONS:
                continue
            
            if file.size > settings.MAX_FILE_SIZE:
                continue
            
            # OCR 처리
            result = await ocr_service.extract_text(file)
            results.append(result)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 OCR 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/result/{filename}")
async def get_result_image(filename: str):
    """처리된 결과 이미지 반환"""
    file_path = os.path.join(settings.RESULTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="결과 이미지를 찾을 수 없습니다.")
    
    return FileResponse(file_path)

@router.delete("/result/{filename}")
async def delete_result_image(filename: str):
    """결과 이미지 삭제"""
    file_path = os.path.join(settings.RESULTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="결과 이미지를 찾을 수 없습니다.")
    
    try:
        os.remove(file_path)
        return {"message": "이미지가 성공적으로 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 삭제 중 오류: {str(e)}")

@router.delete("/results/cleanup")
async def cleanup_all_results():
    """모든 결과 이미지 정리"""
    try:
        files = [f for f in os.listdir(settings.RESULTS_DIR) 
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        deleted_count = 0
        for filename in files:
            file_path = os.path.join(settings.RESULTS_DIR, filename)
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ 이미지 삭제 실패: {filename} - {e}")
        
        return {"message": f"{deleted_count}개의 이미지가 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 정리 중 오류: {str(e)}")

@router.post("/extract-and-analyze", response_model=CombinedResponse)
async def extract_and_analyze_file(
    file: UploadFile = File(...),
    mode: str = "prod",
    gpt_prompt: str = "책 제목 추출"
):
    """OCR + GPT 통합 엔드포인트 (파일 업로드 방식)"""
    try:
        # OCR 처리
        ocr_result = await ocr_service.extract_text(file)
        
        # 텍스트와 바운딩 박스 정보를 함께 구성
        text_with_boxes = ocr_service._format_text_with_boxes(ocr_result.text_boxes)
        
        # GPT 책 제목 추출 (바운딩 박스 정보 포함)
        gpt_result = await gpt_service.extract_book_title_with_boxes(text_with_boxes)
        
        # 총 처리 시간 계산
        total_processing_time_ms = (ocr_result.processing_time_ms or 0) + (gpt_result.response_time_ms or 0)
        
        return CombinedResponse(
            ocr_result=ocr_result,
            gpt_result=gpt_result,
            total_processing_time_ms=total_processing_time_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR+GPT 통합 처리 중 오류: {str(e)}")

@router.post("/extract-and-analyze-test", response_model=CombinedResponse)
async def extract_and_analyze_test(request: CombinedRequest):
    """OCR + GPT 통합 엔드포인트 (테스트 모드 - JSON 요청)"""
    try:
        # OCR 처리
        ocr_result = await ocr_service.extract_text_with_mode(image_path=request.image_url, mode="test")
        
        # 텍스트와 바운딩 박스 정보를 함께 구성
        text_with_boxes = ocr_service._format_text_with_boxes(ocr_result.text_boxes)
        
        # GPT 책 제목 추출 (바운딩 박스 정보 포함)
        gpt_result = await gpt_service.extract_book_title_with_boxes(text_with_boxes)
        
        # 총 처리 시간 계산
        total_processing_time_ms = (ocr_result.processing_time_ms or 0) + (gpt_result.response_time_ms or 0)
        
        return CombinedResponse(
            ocr_result=ocr_result,
            gpt_result=gpt_result,
            total_processing_time_ms=total_processing_time_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR+GPT 통합 처리 중 오류: {str(e)}") 