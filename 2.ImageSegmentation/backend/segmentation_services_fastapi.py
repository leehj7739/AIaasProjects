#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 기반 이미지 세그멘테이션 서비스
YOLO를 사용한 보행자 검출 및 세그멘테이션
"""

import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
from PIL import Image
import requests
from pathlib import Path
import json
import base64
from io import BytesIO
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Union
import asyncio

# FastAPI 관련 import
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# 결과 저장 폴더
RESULTS_DIR = Path('results')
UPLOADS_DIR = Path('uploads')
RESULTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# FastAPI 앱 초기화
app = FastAPI(
    title="YOLO 세그멘테이션 서비스",
    description="YOLO를 사용한 보행자 검출 및 이미지 세그멘테이션 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델 정의
class DetectionResult(BaseModel):
    status: str = Field(..., description="GO 또는 STOP 상태")
    person_count: int = Field(..., description="검출된 보행자 수")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")
    timestamp: str = Field(..., description="처리 시간")
    filename: Optional[str] = Field(None, description="저장된 결과 이미지 파일명")

class HealthResponse(BaseModel):
    status: str = Field(..., description="서버 상태")
    service: str = Field(..., description="서비스명")
    model: str = Field(..., description="사용 중인 모델")
    uptime: str = Field(..., description="서버 가동 시간")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")

# 로깅 함수
def log_with_time(msg: str):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {msg}")

# 전역 변수
last_receive_time = None
start_time = datetime.now()

class SegmentationServices:
    def __init__(self):
        """세그멘테이션 서비스 초기화"""
        log_with_time("🚀 YOLO 모델 로딩 중...")
        self.yolo_model = YOLO('yolov8n-seg.pt')
        
        # MediaPipe 얼굴 랜드마크
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        log_with_time("✅ YOLO 모델 로딩 완료!")

    def detect_objects(self, image):
        """객체 감지 및 세그멘테이션"""
        results = self.yolo_model(image)
        return results

    def detect_face_landmarks(self, image):
        """얼굴 랜드마크 검출"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        return results

    def remove_background(self, image, target_class='person'):
        """특정 객체의 배경 제거"""
        results = self.detect_objects(image)
        
        # 마스크 생성
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        for result in results:
            boxes = result.boxes
            masks = result.masks
            
            if boxes is not None and masks is not None:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    
                    if class_name == target_class:
                        mask_data = masks.data[i].cpu().numpy()
                        mask_resized = cv2.resize(mask_data, (image.shape[1], image.shape[0]))
                        mask = np.maximum(mask, (mask_resized > 0.5).astype(np.uint8) * 255)
        
        # 배경 제거
        result_image = image.copy()
        result_image[mask == 0] = [255, 255, 255]  # 흰색 배경
        
        return result_image, mask

    def extract_objects(self, image, target_classes=None):
        """특정 객체들 추출"""
        results = self.detect_objects(image)
        extracted_objects = []
        
        for result in results:
            boxes = result.boxes
            masks = result.masks
            
            if boxes is not None and masks is not None:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    
                    if target_classes is None or class_name in target_classes:
                        # 마스크 적용
                        mask_data = masks.data[i].cpu().numpy()
                        mask_resized = cv2.resize(mask_data, (image.shape[1], image.shape[0]))
                        mask_bool = mask_resized > 0.5
                        
                        # 객체 추출
                        extracted = image.copy()
                        extracted[~mask_bool] = [255, 255, 255]
                        
                        extracted_objects.append({
                            'class': class_name,
                            'image': extracted,
                            'mask': mask_bool,
                            'bbox': box.xyxy[0].cpu().numpy().tolist()
                        })
        
        return extracted_objects

    def apply_filter_to_object(self, image, target_class='person', filter_type='blur'):
        """특정 객체에 필터 적용"""
        results = self.detect_objects(image)
        result_image = image.copy()
        
        for result in results:
            boxes = result.boxes
            masks = result.masks
            
            if boxes is not None and masks is not None:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    
                    if class_name == target_class:
                        mask_data = masks.data[i].cpu().numpy()
                        mask_resized = cv2.resize(mask_data, (image.shape[1], image.shape[0]))
                        mask_bool = mask_resized > 0.5
                        
                        # 필터 적용
                        if filter_type == 'blur':
                            blurred = cv2.GaussianBlur(result_image, (15, 15), 0)
                            result_image[mask_bool] = blurred[mask_bool]
                        elif filter_type == 'brightness':
                            hsv = cv2.cvtColor(result_image, cv2.COLOR_BGR2HSV)
                            hsv[mask_bool, 2] = np.clip(hsv[mask_bool, 2] * 1.5, 0, 255)
                            result_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result_image

    def apply_face_beauty(self, image):
        """얼굴 뷰티 필터 적용"""
        results = self.detect_face_landmarks(image)
        result_image = image.copy()
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, _ = image.shape
                
                # 얼굴 영역 마스크 생성
                face_mask = np.zeros((h, w), dtype=np.uint8)
                
                # 얼굴 윤곽 랜드마크
                face_oval_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                                   397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                                   172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10]
                
                face_points = []
                for idx in face_oval_indices:
                    if idx < len(face_landmarks.landmark):
                        landmark = face_landmarks.landmark[idx]
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        face_points.append([x, y])
                
                if len(face_points) > 2:
                    # 얼굴 마스크 생성
                    face_points = np.array(face_points, dtype=np.int32)
                    cv2.fillPoly(face_mask, [face_points], 255)
                    
                    # 뷰티 필터 적용
                    # 1. 스무딩 (블러)
                    smoothed = cv2.GaussianBlur(result_image, (5, 5), 0)
                    result_image = np.where(face_mask[:, :, np.newaxis] > 0, 
                                          smoothed, result_image)
                    
                    # 2. 밝기 조정
                    hsv = cv2.cvtColor(result_image, cv2.COLOR_BGR2HSV)
                    hsv[face_mask > 0, 2] = np.clip(hsv[face_mask > 0, 2] * 1.1, 0, 255)
                    result_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result_image

    def count_objects(self, image, target_classes=None, draw_on_image=True):
        """객체 개수 세기"""
        results = self.detect_objects(image)
        counts = {}
        result_image = image.copy() if draw_on_image else None
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    
                    if target_classes is None or class_name in target_classes:
                        counts[class_name] = counts.get(class_name, 0) + 1
                        
                        if draw_on_image:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            
                            # 박스 그리기
                            cv2.rectangle(result_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                            
                            # 라벨 그리기
                            label = f"{class_name} {conf:.2f}"
                            cv2.putText(result_image, label, (int(x1), int(y1)-10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return counts, result_image

    def analyze_image(self, image):
        """이미지 분석"""
        results = self.detect_objects(image)
        analysis = {
            'total_objects': 0,
            'object_counts': {},
            'dominant_objects': [],
            'confidence_scores': [],
            'bounding_boxes': []
        }
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    conf = float(box.conf[0].cpu().numpy())
                    bbox = box.xyxy[0].cpu().numpy().tolist()
                    
                    analysis['total_objects'] += 1
                    analysis['object_counts'][class_name] = analysis['object_counts'].get(class_name, 0) + 1
                    analysis['confidence_scores'].append(conf)
                    analysis['bounding_boxes'].append({
                        'class': class_name,
                        'bbox': bbox,
                        'confidence': conf
                    })
        
        # 주요 객체 찾기
        if analysis['object_counts']:
            max_count = max(analysis['object_counts'].values())
            analysis['dominant_objects'] = [obj for obj, count in analysis['object_counts'].items() if count == max_count]
        
        return analysis

    def create_collage(self, image, layout='grid'):
        """객체 콜라주 생성"""
        extracted_objects = self.extract_objects(image, ['person', 'car', 'dog', 'cat'])
        
        if not extracted_objects:
            return image
        
        # 간단한 그리드 레이아웃
        n_objects = len(extracted_objects)
        cols = min(3, n_objects)
        rows = (n_objects + cols - 1) // cols
        
        # 콜라주 크기 계산
        obj_height, obj_width = extracted_objects[0]['image'].shape[:2]
        collage_height = rows * obj_height
        collage_width = cols * obj_width
        
        collage = np.ones((collage_height, collage_width, 3), dtype=np.uint8) * 255
        
        for i, obj in enumerate(extracted_objects):
            row = i // cols
            col = i % cols
            y_start = row * obj_height
            x_start = col * obj_width
            y_end = y_start + obj_height
            x_end = x_start + obj_width
            
            collage[y_start:y_end, x_start:x_end] = obj['image']
        
        return collage

    def extract_metadata(self, image):
        """이미지 메타데이터 추출"""
        results = self.detect_objects(image)
        metadata = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    conf = float(box.conf[0].cpu().numpy())
                    bbox = box.xyxy[0].cpu().numpy()
                    
                    metadata.append({
                        'type': class_name,
                        'confidence': f"{conf:.2f}",
                        'position': f"({bbox[0]:.0f}, {bbox[1]:.0f})",
                        'size': f"{bbox[2]-bbox[0]:.0f}x{bbox[3]-bbox[1]:.0f}"
                    })
        
        return metadata

# YOLO 모델 로드 (person 클래스만 사용)
model = YOLO('yolov8n-seg.pt')

# 서비스 인스턴스
services = SegmentationServices()

def save_and_limit_dir(directory: Path, filename: str, image: Image.Image) -> str:
    """이미지 저장 및 최대 개수 제한"""
    path = directory / filename
    image.save(path)
    
    # 파일 개수 제한 (최대 30개)
    files = sorted([directory / f for f in os.listdir(directory)], key=os.path.getctime)
    if len(files) > 30:
        for f in files[:-30]:
            try:
                os.remove(f)
            except Exception as e:
                log_with_time(f"[파일 삭제 오류] {f}: {e}")
    
    return str(path)

# 비동기 이미지 처리 함수
async def process_image_async(image_bytes: bytes) -> tuple:
    """비동기 이미지 처리"""
    try:
        # 이미지 디코딩
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("이미지를 읽을 수 없습니다")
        
        # PIL Image로 변환
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # YOLO 추론
        results = model(img)
        person_detected = False
        person_count = 0
        
        # PIL -> numpy 변환
        img_np = np.array(img)
        result_img_np = img_np.copy()
        
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    conf = float(box.conf[0].cpu().numpy())
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    color = (0, 255, 0) if cls == 0 else (255, 0, 0)
                    label = f"{model.names[cls]} {conf:.2f}"
                    
                    # 박스 그리기
                    cv2.rectangle(result_img_np, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(result_img_np, label, (int(x1), int(y1)-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    if cls == 0:  # person 클래스
                        person_detected = True
                        person_count += 1
        
        # 결과 이미지에 보행자 정보 표시
        h, w = result_img_np.shape[:2]
        if person_detected:
            text = f'People: {person_count}'
            color = (0, 0, 255)  # 빨간색
        else:
            text = 'No People'
            color = (0, 255, 0)  # 초록색
        
        # 텍스트 크기 계산
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 좌하단 위치 계산
        text_x = 20
        text_y = h - 20
        
        # 배경 사각형 그리기
        cv2.rectangle(result_img_np, 
                     (text_x - 10, text_y - text_height - 10),
                     (text_x + text_width + 10, text_y + 10),
                     (0, 0, 0), -1)
        
        # 텍스트 그리기
        cv2.putText(result_img_np, text, (text_x, text_y), 
                   font, font_scale, (255, 255, 255), thickness)
        
        result_img_pil = Image.fromarray(result_img_np)
        
        return person_detected, person_count, result_img_pil
        
    except Exception as e:
        log_with_time(f"이미지 처리 오류: {e}")
        raise

# API 엔드포인트

@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "YOLO 세그멘테이션 서비스",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """헬스 체크"""
    uptime = datetime.now() - start_time
    return HealthResponse(
        status="healthy",
        service="YOLO Segmentation Service",
        model="yolov8n-seg.pt",
        uptime=str(uptime).split('.')[0]
    )

@app.post("/detect_person", response_model=DetectionResult)
async def detect_person(
    image: UploadFile = File(..., description="업로드할 이미지 파일"),
    background_tasks: BackgroundTasks = None
):
    """보행자 검출 API (FastAPI 버전)"""
    global last_receive_time
    
    start_time = time.time()
    now = start_time
    
    # 수신 간격 계산
    if last_receive_time is not None:
        interval_ms = int((now - last_receive_time) * 1000)
        log_with_time(f"[detect_person] 이전 요청 대비 수신 간격: {interval_ms} ms")
    last_receive_time = now
    
    log_with_time(f"[detect_person] 요청 수신: {image.filename}")
    
    try:
        # 이미지 읽기
        image_bytes = await image.read()
        
        # 비동기 이미지 처리
        person_detected, person_count, result_img_pil = await process_image_async(image_bytes)
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        base_name = os.path.splitext(image.filename)[0] if image.filename else "unknown"
        upload_filename = f"{timestamp}_{base_name}.jpg"
        result_filename = f"{timestamp}_{base_name}_result.jpg"
        
        # 원본 이미지 저장 (백그라운드)
        if background_tasks:
            background_tasks.add_task(save_and_limit_dir, UPLOADS_DIR, upload_filename, Image.open(BytesIO(image_bytes)))
        
        # 결과 이미지 저장
        save_and_limit_dir(RESULTS_DIR, result_filename, result_img_pil)
        
        # 상태 결정
        status = "stop" if person_detected else "go"
        
        # 처리 시간 계산
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)
        
        log_with_time(f"[detect_person] 결과: {status}, 사람 수: {person_count}명")
        log_with_time(f"[detect_person] 처리~송신까지 소요 시간: {elapsed_ms} ms")
        
        return DetectionResult(
            status=status,
            person_count=person_count,
            processing_time_ms=elapsed_ms,
            timestamp=timestamp,
            filename=result_filename
        )
        
    except Exception as e:
        log_with_time(f"[detect_person] 오류: {e}")
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류 발생: {str(e)}")

@app.post("/api/road_segmentation", response_model=DetectionResult)
async def api_road_segmentation(
    image: UploadFile = File(..., description="도로 이미지 파일")
):
    """도로 세그멘테이션 API (기존 Flask와 호환)"""
    return await detect_person(image)

@app.get("/results/{filename}")
async def get_result_image(filename: str):
    """결과 이미지 다운로드"""
    file_path = RESULTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(file_path)

@app.get("/results")
async def list_results():
    """결과 이미지 목록"""
    files = [f for f in os.listdir(RESULTS_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files.sort(key=lambda x: os.path.getmtime(RESULTS_DIR / x), reverse=True)
    return {"files": files[:10]}  # 최근 10개만

@app.post("/remove_background")
async def remove_background(
    image: UploadFile = File(..., description="이미지 파일"),
    target_class: str = Form("person", description="배경을 제거할 객체 클래스")
):
    """배경 제거 서비스"""
    try:
        image_bytes = await image.read()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        result_image, mask = services.remove_background(image, target_class)
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"bg_removed_{timestamp}.jpg"
        cv2.imwrite(str(RESULTS_DIR / filename), result_image)
        
        return {"filename": filename, "message": "배경 제거 완료"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배경 제거 중 오류: {str(e)}")

@app.post("/extract_objects")
async def extract_objects(
    image: UploadFile = File(..., description="이미지 파일"),
    target_classes: str = Form("person,car", description="추출할 객체 클래스 (쉼표로 구분)")
):
    """객체 추출 서비스"""
    try:
        image_bytes = await image.read()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        classes = [c.strip() for c in target_classes.split(',')]
        extracted_objects = services.extract_objects(image, classes)
        
        return {
            "extracted_count": len(extracted_objects),
            "classes": classes,
            "objects": [{"class": obj['class'], "bbox": obj['bbox']} for obj in extracted_objects]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"객체 추출 중 오류: {str(e)}")

@app.post("/count_objects")
async def count_objects(
    image: UploadFile = File(..., description="이미지 파일"),
    target_classes: str = Form(None, description="세고 싶은 객체 클래스 (쉼표로 구분, 비워두면 모든 객체)")
):
    """객체 개수 세기"""
    try:
        image_bytes = await image.read()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        classes = None
        if target_classes:
            classes = [c.strip() for c in target_classes.split(',')]
        
        counts, result_image = services.count_objects(image, classes, draw_on_image=True)
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"counted_{timestamp}.jpg"
        cv2.imwrite(str(RESULTS_DIR / filename), result_image)
        
        return {
            "counts": counts,
            "total_objects": sum(counts.values()),
            "filename": filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"객체 개수 세기 중 오류: {str(e)}")

@app.post("/analyze_image")
async def analyze_image(image: UploadFile = File(..., description="분석할 이미지 파일")):
    """이미지 분석"""
    try:
        image_bytes = await image.read()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        analysis = services.analyze_image(image)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 분석 중 오류: {str(e)}")

if __name__ == "__main__":
    log_with_time("🚀 FastAPI YOLO 세그멘테이션 서버 시작...")
    log_with_time("📱 웹 인터페이스: http://localhost:8000")
    log_with_time("📚 API 문서: http://localhost:8000/docs")
    log_with_time("🔗 API 엔드포인트: http://localhost:8000/detect_person")
    
    uvicorn.run(
        "segmentation_services_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

