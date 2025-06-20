import cv2
import numpy as np
from PIL import Image
import io
import os
from typing import Tuple, Optional
from fastapi import UploadFile

from app.config.settings import settings

class ImageService:
    @staticmethod
    async def process_image(file: UploadFile) -> np.ndarray:
        """이미지 전처리"""
        try:
            # 파일 읽기
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # OpenCV 형식으로 변환
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            return cv_image
            
        except Exception as e:
            raise Exception(f"이미지 처리 실패: {str(e)}")
    
    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """이미지 품질 향상"""
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # 대비 향상
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 다시 BGR로 변환
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return enhanced_bgr
            
        except Exception as e:
            raise Exception(f"이미지 향상 실패: {str(e)}")
    
    @staticmethod
    def resize_image(image: np.ndarray, max_size: Tuple[int, int] = (1920, 1080)) -> np.ndarray:
        """이미지 리사이즈"""
        try:
            height, width = image.shape[:2]
            max_width, max_height = max_size
            
            # 비율 계산
            scale = min(max_width / width, max_height / height)
            
            if scale < 1:
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                return resized
            
            return image
            
        except Exception as e:
            raise Exception(f"이미지 리사이즈 실패: {str(e)}")
    
    @staticmethod
    def save_image(image: np.ndarray, filepath: str) -> bool:
        """이미지 저장"""
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 이미지 저장
            success = cv2.imwrite(filepath, image)
            return success
            
        except Exception as e:
            raise Exception(f"이미지 저장 실패: {str(e)}")
    
    @staticmethod
    def draw_bounding_boxes(image: np.ndarray, boxes: list, texts: list, confidences: list) -> np.ndarray:
        """바운딩 박스 그리기"""
        try:
            result_image = image.copy()
            
            for i, (box, text, confidence) in enumerate(zip(boxes, texts, confidences)):
                # 박스 좌표
                pts = np.array(box, np.int32)
                pts = pts.reshape((-1, 1, 2))
                
                # 박스 그리기
                cv2.polylines(result_image, [pts], True, (0, 255, 0), 2)
                
                # 텍스트 표시
                x, y = box[0]
                label = f"{text} ({confidence:.2f})"
                cv2.putText(result_image, label, (int(x), int(y) - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            return result_image
            
        except Exception as e:
            raise Exception(f"바운딩 박스 그리기 실패: {str(e)}")
    
    @staticmethod
    def validate_image_format(filename: str) -> bool:
        """이미지 형식 검증"""
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in settings.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_image_size(file_size: int) -> bool:
        """이미지 크기 검증"""
        return file_size <= settings.MAX_FILE_SIZE 