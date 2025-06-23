"""
OCR (Optical Character Recognition) 서비스 모듈

이 모듈은 EasyOCR을 사용하여 이미지에서 텍스트를 추출하는 기능을 제공합니다.
다양한 이미지 전처리 기법을 적용하여 OCR 성능을 최적화합니다.

주요 기능:
- EasyOCR 초기화 및 설정
- 이미지 전처리 (노이즈 제거, 대비 향상, 이진화 등)
- 다중 스케일 처리 (작은 텍스트 포착)
- OCR 결과 필터링 및 후처리
- 박싱 이미지 생성 (텍스트 박스 표시)
- 파일 업로드 및 경로 기반 OCR 지원

전처리 기법:
1. 그레이스케일 변환
2. 노이즈 제거 (가우시안 블러)
3. 대비 향상 (CLAHE)
4. 샤프닝 필터
5. 모폴로지 연산
6. 적응형 이진화
7. 다중 스케일 처리
"""

import easyocr
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
import uuid
from typing import List, Tuple
from fastapi import UploadFile
import time
import re

from app.models.response import OCRResponse
from app.config.settings import settings
from app.core.exceptions import OCRException

class OCRService:
    """
    OCR 서비스 클래스
    
    EasyOCR을 사용하여 이미지에서 텍스트를 추출하는 메인 서비스 클래스입니다.
    다양한 전처리 기법을 적용하여 OCR 성능을 최적화하고,
    결과 이미지에 텍스트 박스를 표시하는 기능을 제공합니다.
    
    주요 메서드:
    - extract_text(): 파일 업로드 기반 OCR
    - extract_text_from_path(): 파일 경로 기반 OCR
    - extract_text_with_mode(): 모드에 따른 OCR (운영/테스트)
    """
    
    def __init__(self):
        """
        EasyOCR 리더 초기화
        
        설정된 언어(한국어, 영어)로 EasyOCR 리더를 초기화합니다.
        GPU 사용이 불가능한 환경을 고려하여 CPU 모드로 설정합니다.
        """
        try:
            print("🔧 EasyOCR 초기화 중...")
            # EasyOCR 리더 초기화
            # settings.OCR_LANGUAGES: ["ko", "en"] (한국어, 영어)
            # gpu=False: CPU 사용 (GPU가 없는 환경에서도 동작)
            # verbose=False: 로그 출력 최소화
            self.reader = easyocr.Reader(
                settings.OCR_LANGUAGES,
                gpu=False,  # CPU 사용으로 변경
                verbose=False  # 로그 줄이기
            )
            print("✅ EasyOCR 초기화 완료")
        except Exception as e:
            print(f"❌ EasyOCR 초기화 실패: {e}")
            # 기본 설정으로 재시도
            try:
                self.reader = easyocr.Reader(['ko', 'en'], gpu=False)
                print("✅ 기본 설정으로 EasyOCR 초기화 완료")
            except Exception as e2:
                raise OCRException(f"EasyOCR 초기화 실패: {str(e2)}")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        이미지 전처리 - OCR 성능 향상을 위한 전처리 (강도 조절)
        
        OCR 성능을 향상시키기 위해 다양한 이미지 처리 기법을 적용합니다.
        강도를 조절하여 텍스트 손실을 최소화하면서 노이즈를 제거합니다.
        
        Args:
            image (np.ndarray): 전처리할 이미지 (OpenCV 형식)
            
        Returns:
            np.ndarray: 전처리된 이미지
        """
        try:
            print("🔍 이미지 전처리 시작...")
            
            # 1. 그레이스케일 변환
            # 컬러 이미지를 그레이스케일로 변환하여 처리 속도 향상
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            print(f"📏 이미지 크기: {gray.shape}")
            
            # 2. 노이즈 제거 (가우시안 블러) - 매우 약한 블러
            # 이미지의 노이즈를 제거하되 텍스트는 보존
            denoised = cv2.GaussianBlur(gray, (1, 1), 0)
            
            # 3. 적응형 히스토그램 평활화 (CLAHE) - 대비 향상 (약한 강도)
            # 이미지의 대비를 향상시켜 텍스트를 더 명확하게 만듦
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 4. 샤프닝 필터 적용 (약한 강도)
            # 텍스트의 경계를 더 명확하게 만듦
            kernel_sharpen = np.array([[-0.5,-0.5,-0.5], [-0.5,5,-0.5], [-0.5,-0.5,-0.5]])
            sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)
            
            # 5. 모폴로지 연산 (최소한의 적용)
            # 텍스트 영역을 연결하고 작은 노이즈 제거
            kernel = np.ones((1, 1), np.int32)
            morph = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, kernel)
            
            # 6. 적응형 이진화 (더 관대한 설정)
            # 그레이스케일 이미지를 이진 이미지로 변환
            # 블록 크기와 C값을 조정하여 텍스트 손실 최소화
            binary = cv2.adaptiveThreshold(
                morph, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 3  # 블록 크기 증가, C값 증가
            )
            
            # 7. 노이즈 제거 (최소한의 모폴로지)
            # 작은 노이즈를 제거하되 텍스트는 보존
            kernel_clean = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_clean)
            
            print("✅ 이미지 전처리 완료")
            return cleaned
            
        except Exception as e:
            print(f"⚠️ 전처리 실패, 원본 이미지 사용: {e}")
            return image
    
    def _preprocess_multiscale(self, image: np.ndarray) -> list:
        """다중 스케일 전처리 - 여러 크기로 처리하여 작은 텍스트도 포착 (강도 조절)"""
        try:
            preprocessed_images = []
            
            # 원본 크기 (약한 전처리)
            preprocessed_images.append(self._preprocess_image(image))
            
            # 1.2배 확대 (약한 전처리)
            height, width = image.shape[:2]
            enlarged = cv2.resize(image, (int(width * 1.2), int(height * 1.2)), interpolation=cv2.INTER_LINEAR)
            preprocessed_images.append(self._preprocess_image(enlarged))
            
            # 1.5배 확대 (약한 전처리)
            enlarged_15x = cv2.resize(image, (int(width * 1.5), int(height * 1.5)), interpolation=cv2.INTER_LINEAR)
            preprocessed_images.append(self._preprocess_image(enlarged_15x))
            
            return preprocessed_images
            
        except Exception as e:
            print(f"⚠️ 다중 스케일 전처리 실패: {e}")
            return [self._preprocess_image(image)]
    
    def _enhance_small_text(self, image: np.ndarray) -> np.ndarray:
        """작은 텍스트 강화 전처리 (약한 강도)"""
        try:
            # 1. 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 2. 언샤프 마스킹 (약한 강도)
            gaussian = cv2.GaussianBlur(gray, (0, 0), 1.5)
            unsharp_mask = cv2.addWeighted(gray, 1.3, gaussian, -0.3, 0)
            
            # 3. 대비 강화 (약한 강도)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(unsharp_mask)
            
            # 4. 이진화 (Otsu 방법 사용)
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
            
        except Exception as e:
            print(f"⚠️ 작은 텍스트 강화 실패: {e}")
            return image
    
    def _preprocess_original(self, image: np.ndarray) -> np.ndarray:
        """원본 이미지 기반 전처리 (최소한의 처리)"""
        try:
            # 1. 그레이스케일 변환
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 2. 매우 약한 대비 향상
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 3. 적응형 이진화 (관대한 설정)
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 21, 5
            )
            
            return binary
            
        except Exception as e:
            print(f"⚠️ 원본 전처리 실패: {e}")
            return image
    
    def _resize_image(self, image: np.ndarray, max_size: int = 1024) -> np.ndarray:
        """이미지 크기 조정 - 너무 큰 이미지 처리 속도 향상"""
        height, width = image.shape[:2]
        
        if max(height, width) > max_size:
            # 비율 유지하면서 크기 조정
            scale = max_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            print(f"📏 이미지 크기 조정: {width}x{height} → {new_width}x{new_height}")
            return resized
        
        return image
    
    async def _perform_ocr(self, image: np.ndarray) -> list:
        """
        이미지에서 OCR 수행
        
        Args:
            image (np.ndarray): OCR 처리할 이미지
            
        Returns:
            list: OCR 결과 리스트
        """
        try:
            print("🔍 OCR 처리 시작...")
            
            # 원본 이미지로 먼저 OCR 시도
            print("🔍 원본 이미지로 OCR 시도...")
            original_results = self.reader.readtext(image)
            print(f"📊 원본 이미지 OCR 결과: {len(original_results)}개 텍스트 발견")
            
            if original_results:
                for i, (bbox, text, conf) in enumerate(original_results[:3]):
                    print(f"  {i+1}. '{text}' (신뢰도: {conf:.2f})")
                return original_results
            
            # 원본에서 결과가 없으면 전처리 시도
            print("⚠️ 원본 이미지에서 텍스트를 찾지 못했습니다. 전처리 시도...")
            
            # 다양한 전처리 방법 적용
            preprocessed_images = []
            
            # 1. 원본 이미지 기반 전처리 (최소한의 처리)
            print("🔍 원본 기반 전처리 적용...")
            preprocessed_images.append(self._preprocess_original(image))
            
            # 2. 다중 스케일 전처리 적용 (약한 강도)
            print("🔍 다중 스케일 전처리 적용...")
            multiscale_images = self._preprocess_multiscale(image)
            preprocessed_images.extend(multiscale_images)
            
            # 3. 작은 텍스트 강화 전처리도 추가 (약한 강도)
            print("🔍 작은 텍스트 강화 전처리 적용...")
            small_text_enhanced = self._enhance_small_text(image)
            preprocessed_images.append(small_text_enhanced)
            
            # 4. 원본 이미지도 직접 사용 (전처리 없이)
            print("🔍 원본 이미지 직접 사용...")
            preprocessed_images.append(image)
            
            # 모든 전처리된 이미지에서 OCR 수행
            all_results = []
            for i, preprocessed_image in enumerate(preprocessed_images):
                print(f"🔍 전처리 이미지 {i+1}/{len(preprocessed_images)}에서 OCR 수행...")
                try:
                    results = self.reader.readtext(preprocessed_image)
                    print(f"  → {len(results)}개 텍스트 발견")
                    all_results.extend(results)
                except Exception as e:
                    print(f"  → OCR 실패: {e}")
            
            return all_results
            
        except Exception as e:
            print(f"❌ OCR 수행 실패: {e}")
            return []
    
    async def _save_result_image(self, result_image: np.ndarray, original_filename: str) -> str:
        """
        결과 이미지 저장
        
        Args:
            result_image (np.ndarray): 저장할 결과 이미지
            original_filename (str): 원본 파일명
            
        Returns:
            str: 저장된 이미지 경로
        """
        try:
            # 파일명 생성
            filename = f"{uuid.uuid4()}.jpg"
            result_path = os.path.join(settings.RESULTS_DIR, filename)
            
            # 이미지 저장
            cv2.imwrite(result_path, result_image)
            print(f"💾 결과 이미지 저장: {result_path}")
            
            # 이미지 개수 제한 적용 (20개 유지)
            await self._limit_result_images()
            
            return filename
            
        except Exception as e:
            print(f"⚠️ 결과 이미지 저장 실패: {e}")
            return None
    
    async def _limit_result_images(self):
        """결과 이미지 개수를 20개로 제한하고 오래된 이미지 삭제"""
        try:
            # 결과 디렉토리의 모든 이미지 파일 확인
            files = [f for f in os.listdir(settings.RESULTS_DIR) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            # 20개를 초과하는 경우
            if len(files) > settings.MAX_RESULT_IMAGES:
                # 파일 경로와 생성 시간을 함께 저장
                file_times = []
                for filename in files:
                    file_path = os.path.join(settings.RESULTS_DIR, filename)
                    if os.path.exists(file_path):
                        creation_time = os.path.getctime(file_path)
                        file_times.append((file_path, creation_time))
                
                # 생성 시간 기준으로 정렬 (오래된 것부터)
                file_times.sort(key=lambda x: x[1])
                
                # 가장 오래된 파일들 삭제 (20개 초과분만)
                files_to_delete = file_times[:-settings.MAX_RESULT_IMAGES]
                
                for file_path, _ in files_to_delete:
                    try:
                        os.remove(file_path)
                        print(f"🗑️ 오래된 결과 이미지 삭제: {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"⚠️ 이미지 삭제 실패: {file_path} - {e}")
                
                print(f"✅ 결과 이미지 개수 제한 적용: {len(files)} → {settings.MAX_RESULT_IMAGES}")
                        
        except Exception as e:
            print(f"⚠️ 이미지 개수 제한 처리 중 오류: {e}")
    
    def _convert_results_to_python(self, results):
        """OCR 결과의 numpy 타입을 파이썬 기본 타입으로 변환"""
        converted = []
        for bbox, text, confidence in results:
            bbox_py = [[float(x), float(y)] for x, y in bbox]
            converted.append((bbox_py, str(text), float(confidence)))
        return converted

    async def extract_text(self, file: UploadFile) -> OCRResponse:
        """
        파일 업로드 기반 텍스트 추출
        
        Args:
            file (UploadFile): 업로드된 이미지 파일
            
        Returns:
            OCRResponse: OCR 처리 결과
        """
        start_time = time.time()
        
        try:
            print(f"📁 파일 처리 시작: {file.filename}")
            
            # 파일 내용 읽기
            file_content = await file.read()
            image_array = np.frombuffer(file_content, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise OCRException("이미지를 읽을 수 없습니다.")
            
            print(f"📏 원본 이미지 크기: {image.shape}")
            
            # 이미지 크기 조정 (너무 큰 이미지 처리)
            image = self._resize_image(image)
            
            # OCR 처리
            results = await self._perform_ocr(image)
            
            # 결과 필터링 및 병합
            filtered_results = self._filter_and_merge_results(results)
            
            # 추출된 텍스트 생성
            extracted_text = "\n".join([result[1] for result in filtered_results])
            
            # 처리 시간 계산
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 결과 이미지 생성 (설정에 따라 저장)
            result_image_path = None
            if settings.SAVE_RESULT_IMAGES:
                result_image = self._create_result_image(image, filtered_results)
                result_image_path = await self._save_result_image(result_image, file.filename)
            
            print(f"✅ OCR 처리 완료 - 텍스트 길이: {len(extracted_text)}")
            
            return OCRResponse(
                extracted_text=extracted_text,
                confidence_scores=[float(result[2]) for result in filtered_results],
                processing_time_ms=processing_time_ms,
                result_image_path=result_image_path,
                text_boxes=self._convert_results_to_python(filtered_results)
            )
            
        except Exception as e:
            print(f"❌ OCR 처리 실패: {e}")
            raise OCRException(f"OCR 처리 중 오류가 발생했습니다: {str(e)}")
    
    def _filter_and_merge_results(self, all_results: list) -> list:
        """OCR 결과 중복 제거 및 신뢰도 기반 필터링"""
        try:
            # 텍스트별로 그룹화
            text_groups = {}
            for bbox, text, confidence in all_results:
                # 텍스트 정규화 (공백 제거, 소문자 변환)
                normalized_text = text.strip().lower()
                
                if normalized_text not in text_groups:
                    text_groups[normalized_text] = []
                
                text_groups[normalized_text].append((bbox, text, confidence))
            
            # 각 그룹에서 최고 신뢰도 결과 선택
            filtered_results = []
            for normalized_text, group in text_groups.items():
                # 신뢰도 기준으로 정렬
                group.sort(key=lambda x: x[2], reverse=True)
                best_result = group[0]
                
                # 최소 신뢰도 임계값 적용 (너무 낮은 신뢰도 제거)
                if best_result[2] > 0.1:  # 10% 이상 신뢰도
                    filtered_results.append(best_result)
            
            # 신뢰도 기준으로 정렬
            filtered_results.sort(key=lambda x: x[2], reverse=True)
            
            print(f"📊 OCR 결과 필터링: {len(all_results)} → {len(filtered_results)}")
            return filtered_results
            
        except Exception as e:
            print(f"⚠️ 결과 필터링 실패: {e}")
            return all_results
    
    def _create_result_image(self, image: np.ndarray, results: List[Tuple]) -> np.ndarray:
        """결과 이미지 생성 (텍스트 박스 표시) - 한글 지원"""
        # OpenCV 이미지를 PIL 이미지로 변환
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_image)
        
        # 폰트 설정 (한글 폰트 우선 시도)
        font = None
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",  # 맑은 고딕
            "C:/Windows/Fonts/gulim.ttc",   # 굴림
            "C:/Windows/Fonts/batang.ttc",  # 바탕
            "C:/Windows/Fonts/dotum.ttc",   # 돋움
            "arial.ttf",                    # Arial
            "malgun.ttf"                    # 맑은 고딕 (상대 경로)
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 20)
                print(f"✅ 폰트 로드 성공: {font_path}")
                break
            except Exception as e:
                print(f"❌ 폰트 로드 실패: {font_path} - {e}")
                continue
        
        if font is None:
            print("⚠️ 기본 폰트 사용")
            font = ImageFont.load_default()
        
        for (bbox, text, confidence) in results:
            # 바운딩 박스 좌표
            pts = np.array(bbox, np.int32)
            
            # PIL 이미지에 박스 그리기
            draw.polygon([tuple(point) for point in pts], outline=(0, 255, 0), width=2)
            
            # 텍스트 위치 계산
            x, y = bbox[0]
            text_x, text_y = int(x), int(y) - 25
            
            # 텍스트 배경 그리기 (가독성 향상)
            try:
                bbox_text = draw.textbbox((text_x, text_y), text, font=font)
                draw.rectangle(bbox_text, fill=(0, 0, 0))
                draw.text((text_x, text_y), text, fill=(0, 255, 0), font=font)
            except Exception as e:
                print(f"⚠️ 텍스트 그리기 실패: {e}")
                # 폰트 오류 시 기본 방식 사용
                draw.text((text_x, text_y), text, fill=(0, 255, 0))
        
        # PIL 이미지를 OpenCV 형식으로 변환
        result_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return result_image
    
    async def extract_text_from_path(self, image_path: str) -> OCRResponse:
        """파일 경로에서 텍스트 추출"""
        try:
            print(f"🔍 파일 경로 OCR 시작: {image_path}")
            
            image = cv2.imread(image_path)
            if image is None:
                raise OCRException("이미지를 읽을 수 없습니다.")
            
            print(f"📏 원본 이미지 크기: {image.shape}")
            
            # 이미지 크기 조정
            image = self._resize_image(image)
            print(f"📏 리사이즈 후 이미지 크기: {image.shape}")
            
            # 원본 이미지로 먼저 OCR 시도
            print("🔍 원본 이미지로 OCR 시도...")
            original_results = self.reader.readtext(image)
            print(f"📊 원본 이미지 OCR 결과: {len(original_results)}개 텍스트 발견")
            
            if original_results:
                for i, (bbox, text, conf) in enumerate(original_results[:3]):
                    print(f"  {i+1}. '{text}' (신뢰도: {conf:.2f})")
            
            # 원본에서 결과가 없으면 전처리 시도
            if not original_results:
                print("⚠️ 원본 이미지에서 텍스트를 찾지 못했습니다. 전처리 시도...")
                
                # 이미지 전처리
                preprocessed_image = self._preprocess_image(image)
                print("🔍 전처리된 이미지로 OCR 시도...")
                
                preprocessed_results = self.reader.readtext(preprocessed_image)
                print(f"📊 전처리 이미지 OCR 결과: {len(preprocessed_results)}개 텍스트 발견")
                
                if preprocessed_results:
                    for i, (bbox, text, conf) in enumerate(preprocessed_results[:3]):
                        print(f"  {i+1}. '{text}' (신뢰도: {conf:.2f})")
                
                results = preprocessed_results if preprocessed_results else original_results
            else:
                results = original_results
            
            extracted_text = []
            bounding_boxes = []
            
            for (bbox, text, confidence) in results:
                extracted_text.append(text)
                # numpy 타입을 Python 기본 타입으로 변환
                converted_bbox = [[float(x), float(y)] for x, y in bbox]
                bounding_boxes.append(converted_bbox)
            
            print(f"📊 최종 OCR 결과: {len(extracted_text)}개 텍스트")
            if extracted_text:
                print(f"📝 추출된 텍스트: {' '.join(extracted_text)}")
            
            return OCRResponse(
                extracted_text=" ".join(extracted_text),
                confidence_scores=[float(conf) for _, _, conf in results],
                processing_time_ms=None,
                result_image_path=None,
                text_boxes=self._convert_results_to_python(results)
            )
            
        except Exception as e:
            print(f"❌ 파일 경로 OCR 실패: {e}")
            raise OCRException(f"파일 경로에서 텍스트 추출 실패: {str(e)}")
    
    async def extract_text_with_mode(self, file: UploadFile = None, image_path: str = None, mode: str = "prod"):
        """
        mode에 따라 업로드 파일 또는 경로 기반 이미지에서 OCR 수행
        """
        if mode == "test" and image_path:
            # 경로 기반 OCR (테스트용)
            return await self.extract_text_from_path(image_path)
        elif file:
            # 업로드 파일 OCR (운영용)
            return await self.extract_text(file)
        else:
            raise OCRException("파일 또는 이미지 경로가 필요합니다.")

    def _clean_text(self, text: str) -> str:
        """텍스트에서 특수문자 제거 및 정리"""
        # 한글, 영어, 숫자, 공백만 허용
        cleaned = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)
        
        # 연속된 공백을 하나로 정리
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 앞뒤 공백 제거
        cleaned = cleaned.strip()
        
        return cleaned

    def _format_text_with_boxes(self, text_boxes):
        """텍스트와 바운딩 박스 정보를 함께 포맷팅"""
        if not text_boxes:
            return ""
        
        formatted_lines = []
        for i, (bbox, text, confidence) in enumerate(text_boxes):
            # 텍스트에서 특수문자 제거
            cleaned_text = self._clean_text(text)
            
            # 빈 텍스트는 건너뛰기
            if not cleaned_text:
                continue
            
            # 바운딩 박스 좌표 추출
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            
            # 위치 정보 계산
            left = min(x_coords)
            top = min(y_coords)
            right = max(x_coords)
            bottom = max(y_coords)
            
            # 텍스트와 위치 정보를 함께 포맷팅
            line = f"[{i+1}] 텍스트: '{cleaned_text}' | 위치: ({left:.0f}, {top:.0f}) ~ ({right:.0f}, {bottom:.0f}) | 신뢰도: {confidence:.2f}"
            formatted_lines.append(line)
        
        return "\n".join(formatted_lines) 