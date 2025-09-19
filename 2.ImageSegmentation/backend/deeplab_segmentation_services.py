#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepLabV3+ PyTorch를 사용한 도로 세그멘테이션 서비스
도로, 차선, 보행자, 신호등, 표지판 등을 픽셀 단위로 분할
"""

import cv2
import numpy as np
import torch
import torchvision
from torchvision import transforms
from PIL import Image, ImageFilter, ImageEnhance
import requests
from pathlib import Path
import json
import base64
from io import BytesIO
from flask import Flask, request, jsonify, render_template, send_file, Response
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

app = Flask(__name__)

# 결과 저장 폴더
RESULTS_DIR = Path('results')
RESULTS_DIR.mkdir(exist_ok=True)

def log_with_time(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {msg}")

last_receive_time = None

class DeepLabSegmentationServices:
    def __init__(self, model_name='deeplabv3_mobilenet_v3_large', num_classes=21):
        """DeepLabV3+ 세그멘테이션 서비스 초기화 (경량화)"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        log_with_time(f"🚀 DeepLabV3+ 모델 로딩 중... (Device: {self.device})")
        
        # DeepLabV3+ 모델 로드 (경량화된 MobileNet 사용)
        self.model = self.load_deeplab_model(model_name, num_classes)
        self.model.eval()
        
        # 이미지 전처리 변환 (더 작은 입력 크기로 속도 향상)
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),  # 513 -> 256으로 축소
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # COCO 데이터셋 클래스 정의 (도로 관련 클래스 포함)
        self.class_names = {
            0: 'background', 1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle',
            5: 'airplane', 6: 'bus', 7: 'train', 8: 'truck', 9: 'boat',
            10: 'traffic light', 11: 'fire hydrant', 12: 'stop sign', 13: 'parking meter',
            14: 'bench', 15: 'bird', 16: 'cat', 17: 'dog', 18: 'horse', 19: 'sheep',
            20: 'cow', 21: 'elephant', 22: 'bear', 23: 'zebra', 24: 'giraffe',
            25: 'backpack', 26: 'umbrella', 27: 'handbag', 28: 'tie', 29: 'suitcase',
            30: 'frisbee', 31: 'skis', 32: 'snowboard', 33: 'sports ball', 34: 'kite',
            35: 'baseball bat', 36: 'baseball glove', 37: 'skateboard', 38: 'surfboard',
            39: 'tennis racket', 40: 'bottle', 41: 'wine glass', 42: 'cup', 43: 'fork',
            44: 'knife', 45: 'spoon', 46: 'bowl', 47: 'banana', 48: 'apple',
            49: 'sandwich', 50: 'orange', 51: 'broccoli', 52: 'carrot', 53: 'hot dog',
            54: 'pizza', 55: 'donut', 56: 'cake', 57: 'chair', 58: 'couch',
            59: 'potted plant', 60: 'bed', 61: 'dining table', 62: 'toilet', 63: 'tv',
            64: 'laptop', 65: 'mouse', 66: 'remote', 67: 'keyboard', 68: 'cell phone',
            69: 'microwave', 70: 'oven', 71: 'toaster', 72: 'sink', 73: 'refrigerator',
            74: 'book', 75: 'clock', 76: 'vase', 77: 'scissors', 78: 'teddy bear',
            79: 'hair drier', 80: 'toothbrush'
        }
        
        # 도로 관련 클래스들
        self.road_classes = {
            'person': 1, 'car': 3, 'motorcycle': 4, 'bus': 6, 'truck': 8,
            'traffic light': 10, 'stop sign': 12, 'bicycle': 2
        }
        
        # 클래스별 색상 정의
        self.class_colors = self.generate_class_colors()
        
        log_with_time("✅ DeepLabV3+ 모델 로딩 완료!")

    def load_deeplab_model(self, model_name, num_classes):
        """DeepLabV3+ 모델 로드"""
        try:
            log_with_time(f"모델 로딩 시작: {model_name}")
            
            if model_name == 'deeplabv3_resnet101':
                log_with_time("ResNet101 기반 DeepLabV3+ 로딩 중...")
                model = torchvision.models.segmentation.deeplabv3_resnet101(
                    pretrained=True, progress=True
                )
            elif model_name == 'deeplabv3_resnet50':
                log_with_time("ResNet50 기반 DeepLabV3+ 로딩 중...")
                model = torchvision.models.segmentation.deeplabv3_resnet50(
                    pretrained=True, progress=True
                )
            elif model_name == 'deeplabv3_mobilenet_v3_large':
                log_with_time("MobileNet V3 Large 기반 DeepLabV3+ 로딩 중...")
                model = torchvision.models.segmentation.deeplabv3_mobilenet_v3_large(
                    pretrained=True, progress=True
                )
            else:
                raise ValueError(f"지원하지 않는 모델: {model_name}")
            
            log_with_time("모델을 디바이스로 이동 중...")
            model = model.to(self.device)
            
            log_with_time("모델 평가 모드로 설정...")
            model.eval()
            
            log_with_time("모델 로딩 완료!")
            return model
            
        except Exception as e:
            log_with_time(f"❌ 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            
            # 폴백: 더 가벼운 모델 사용
            try:
                log_with_time("폴백: MobileNet V3 Large 기반 모델 시도...")
                model = torchvision.models.segmentation.deeplabv3_mobilenet_v3_large(
                    pretrained=True, progress=True
                ).to(self.device)
                model.eval()
                log_with_time("폴백 모델 로딩 성공!")
                return model
            except Exception as e2:
                log_with_time(f"❌ 폴백 모델도 실패: {e2}")
                # 최종 폴백: 기본 분류 모델
                log_with_time("최종 폴백: 기본 MobileNet V3 사용...")
                model = torchvision.models.mobilenet_v3_large(pretrained=True).to(self.device)
                model.eval()
                return model

    def generate_class_colors(self):
        """클래스별 색상 생성"""
        colors = {}
        for class_id, class_name in self.class_names.items():
            # 랜덤 색상 생성 (도로 관련 클래스는 특별한 색상)
            if class_name in ['car', 'truck', 'bus']:
                colors[class_id] = [255, 0, 0]  # 빨간색
            elif class_name == 'person':
                colors[class_id] = [0, 255, 0]  # 녹색
            elif class_name == 'traffic light':
                colors[class_id] = [255, 255, 0]  # 노란색
            elif class_name == 'stop sign':
                colors[class_id] = [255, 0, 255]  # 마젠타
            elif class_name in ['bicycle', 'motorcycle']:
                colors[class_id] = [0, 255, 255]  # 청록색
            else:
                colors[class_id] = [np.random.randint(0, 255) for _ in range(3)]
        
        return colors

    def preprocess_image(self, image):
        """이미지 전처리"""
        if isinstance(image, np.ndarray):
            # OpenCV BGR -> RGB 변환
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
        
        # 원본 크기 저장
        original_size = image.size
        
        # 모델 입력용 전처리
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        return input_tensor, original_size

    def segment_image(self, image):
        """이미지 세그멘테이션 수행"""
        try:
            # 이미지 전처리
            input_tensor, original_size = self.preprocess_image(image)
            
            # 추론
            with torch.no_grad():
                output = self.model(input_tensor)['out']
            
            # 후처리
            predictions = torch.argmax(output, dim=1)
            predictions = predictions.squeeze().cpu().numpy()
            
            # 원본 크기로 리사이즈
            predictions = cv2.resize(predictions.astype(np.uint8), 
                                   (original_size[0], original_size[1]), 
                                   interpolation=cv2.INTER_NEAREST)
            
            return predictions
            
        except Exception as e:
            log_with_time(f"❌ 세그멘테이션 실패: {e}")
            return None

    def create_segmentation_visualization(self, image, segmentation_map):
        """세그멘테이션 결과 시각화"""
        if segmentation_map is None:
            return image
        
        # 원본 이미지 복사
        vis_image = image.copy()
        
        # 세그멘테이션 마스크 오버레이
        overlay = np.zeros_like(image)
        
        for class_id in np.unique(segmentation_map):
            if class_id == 0:  # 배경은 건너뛰기
                continue
            
            mask = (segmentation_map == class_id)
            color = self.class_colors.get(class_id, [128, 128, 128])
            
            overlay[mask] = color
        
        # 알파 블렌딩으로 오버레이
        alpha = 0.6
        vis_image = cv2.addWeighted(vis_image, 1-alpha, overlay, alpha, 0)
        
        return vis_image

    def create_road_visualization_with_boxes(self, image, segmentation_map, road_objects):
        """바운딩 박스와 보행자 정보가 포함된 도로 시각화"""
        if segmentation_map is None:
            return image
        
        # 원본 이미지 복사
        vis_image = image.copy()
        
        # 세그멘테이션 마스크 오버레이
        overlay = np.zeros_like(image)
        
        for class_id in np.unique(segmentation_map):
            if class_id == 0:  # 배경은 건너뛰기
                continue
            
            mask = (segmentation_map == class_id)
            color = self.class_colors.get(class_id, [128, 128, 128])
            
            overlay[mask] = color
        
        # 알파 블렌딩으로 오버레이
        alpha = 0.6
        vis_image = cv2.addWeighted(vis_image, 1-alpha, overlay, alpha, 0)
        
        # 바운딩 박스 그리기
        person_count = 0
        for obj in road_objects:
            bbox = obj['bbox']
            class_name = obj['class_name']
            area = obj['area']
            
            # 클래스별 색상
            if class_name == 'person':
                color = (0, 255, 0)  # 녹색 (BGR)
                person_count += 1
            elif class_name in ['car', 'truck', 'bus']:
                color = (0, 0, 255)  # 빨간색 (BGR)
            elif class_name == 'traffic light':
                color = (0, 255, 255)  # 청록색 (BGR)
            elif class_name == 'stop sign':
                color = (255, 0, 255)  # 마젠타 (BGR)
            else:
                color = (255, 255, 0)  # 청록색 (BGR)
            
            # 바운딩 박스 그리기
            x1, y1, x2, y2 = bbox
            cv2.rectangle(vis_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # 라벨 그리기
            label = f"{class_name} {area:.0f}"
            cv2.putText(vis_image, label, (int(x1), int(y1)-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 좌하단에 보행자 검출 정보 표시
        h, w = vis_image.shape[:2]
        
        if person_count > 0:
            # 보행자 감지 시 - 빨간색
            text = f'People: {person_count}'
            text_color = (0, 0, 255)  # 빨간색 (BGR)
            bg_color = (0, 0, 0)  # 검은색 배경
        else:
            # 보행자 비감지 시 - 초록색
            text = 'No People'
            text_color = (0, 255, 0)  # 초록색 (BGR)
            bg_color = (0, 0, 0)  # 검은색 배경
        
        # 텍스트 크기 계산
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 좌하단 위치 계산 (여백 20픽셀)
        text_x = 20
        text_y = h - 20
        
        # 배경 사각형 그리기
        cv2.rectangle(vis_image, 
                     (text_x - 10, text_y - text_height - 10),
                     (text_x + text_width + 10, text_y + 10),
                     bg_color, -1)
        
        # 텍스트 그리기
        cv2.putText(vis_image, text, (text_x, text_y), 
                   font, font_scale, (255, 255, 255), thickness)
        
        return vis_image, person_count

    def extract_road_objects(self, image, segmentation_map):
        """도로 관련 객체 추출"""
        if segmentation_map is None:
            return []
        
        # 디버깅: 실제 검출된 클래스 ID 확인
        unique_classes = np.unique(segmentation_map)
        log_with_time(f"[DEBUG] 검출된 클래스 ID: {unique_classes}")
        
        # 각 클래스 ID별 픽셀 수 확인
        for class_id in unique_classes:
            if class_id > 0:  # 배경 제외
                pixel_count = np.sum(segmentation_map == class_id)
                class_name = self.class_names.get(class_id, f'unknown_{class_id}')
                log_with_time(f"[DEBUG] 클래스 {class_id} ({class_name}): {pixel_count} 픽셀")
        
        road_objects = []
        
        for class_name, class_id in self.road_classes.items():
            mask = (segmentation_map == class_id)
            
            if np.any(mask):
                log_with_time(f"[DEBUG] {class_name} (ID: {class_id}) 검출됨")
                # 바운딩 박스 계산
                contours, _ = cv2.findContours(mask.astype(np.uint8), 
                                             cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    if cv2.contourArea(contour) > 100:  # 최소 면적 필터
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        road_objects.append({
                            'class_name': class_name,
                            'class_id': class_id,
                            'bbox': [x, y, x+w, y+h],
                            'area': cv2.contourArea(contour),
                            'mask': mask[y:y+h, x:x+w]
                        })
                        log_with_time(f"[DEBUG] {class_name} 객체 추가: bbox={[x, y, x+w, y+h]}, area={cv2.contourArea(contour):.0f}")
            else:
                log_with_time(f"[DEBUG] {class_name} (ID: {class_id}) 검출되지 않음")
        
        log_with_time(f"[DEBUG] 총 {len(road_objects)}개 도로 객체 추출됨")
        return road_objects

    def analyze_road_scene(self, image, segmentation_map):
        """도로 장면 분석"""
        if segmentation_map is None:
            return {}
        
        analysis = {
            'objects_detected': [],
            'road_safety_score': 0,
            'traffic_density': 0,
            'pedestrian_count': 0,
            'vehicle_count': 0,
            'traffic_signals': 0
        }
        
        # 객체별 통계
        for class_name, class_id in self.road_classes.items():
            count = np.sum(segmentation_map == class_id)
            
            if count > 0:
                analysis['objects_detected'].append({
                    'class': class_name,
                    'count': int(count),
                    'pixel_coverage': float(count / segmentation_map.size * 100)
                })
                
                # 카테고리별 카운트
                if class_name == 'person':
                    analysis['pedestrian_count'] = int(count)
                elif class_name in ['car', 'truck', 'bus', 'motorcycle']:
                    analysis['vehicle_count'] += int(count)
                elif class_name == 'traffic light':
                    analysis['traffic_signals'] = int(count)
        
        # 교통 밀도 계산
        total_road_objects = analysis['pedestrian_count'] + analysis['vehicle_count']
        analysis['traffic_density'] = min(total_road_objects / 10.0, 1.0)  # 0-1 정규화
        
        # 안전 점수 계산 (간단한 예시)
        safety_score = 100
        if analysis['pedestrian_count'] > 0:
            safety_score -= analysis['pedestrian_count'] * 10
        if analysis['vehicle_count'] > 5:
            safety_score -= (analysis['vehicle_count'] - 5) * 5
        
        analysis['road_safety_score'] = max(safety_score, 0)
        
        return analysis

    def create_lane_detection_mask(self, segmentation_map):
        """차선 감지 마스크 생성 (도로 클래스 기반)"""
        if segmentation_map is None:
            return None
        
        # 도로 관련 클래스들을 차선으로 간주
        lane_mask = np.zeros_like(segmentation_map, dtype=np.uint8)
        
        for class_name, class_id in self.road_classes.items():
            if class_name in ['car', 'truck', 'bus']:  # 차량 클래스
                lane_mask[segmentation_map == class_id] = 255
        
        return lane_mask

    def get_distance_estimation(self, segmentation_map, object_class='person'):
        """객체까지의 거리 추정 (바운딩 박스 크기 기반)"""
        if segmentation_map is None:
            return None
        
        class_id = self.road_classes.get(object_class)
        if class_id is None:
            return None
        
        mask = (segmentation_map == class_id)
        if not np.any(mask):
            return None
        
        # 바운딩 박스 계산
        contours, _ = cv2.findContours(mask.astype(np.uint8), 
                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # 가장 큰 객체 선택
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # 간단한 거리 추정 (바운딩 박스 크기 기반)
        # 실제로는 카메라 캘리브레이션이 필요
        area = w * h
        estimated_distance = 1000 / (area ** 0.5)  # 픽셀 면적의 제곱근으로 거리 추정
        
        return {
            'distance': estimated_distance,
            'bbox': [x, y, x+w, y+h],
            'area': area,
            'confidence': min(area / 1000, 1.0)  # 면적 기반 신뢰도
        }

    def process_image_for_autonomous_driving(self, image):
        """자율주행을 위한 이미지 처리"""
        # 세그멘테이션 수행
        segmentation_map = self.segment_image(image)
        
        if segmentation_map is None:
            return None
        
        # 도로 객체 추출
        road_objects = self.extract_road_objects(image, segmentation_map)
        
        # 장면 분석
        scene_analysis = self.analyze_road_scene(image, segmentation_map)
        
        # 거리 추정
        distance_info = {}
        for obj_class in ['person', 'car']:
            dist = self.get_distance_estimation(segmentation_map, obj_class)
            if dist:
                distance_info[obj_class] = dist
        
        # 시각화
        visualization, person_count = self.create_road_visualization_with_boxes(image, segmentation_map, road_objects)
        
        return {
            'segmentation_map': segmentation_map,
            'road_objects': road_objects,
            'scene_analysis': scene_analysis,
            'distance_info': distance_info,
            'visualization': visualization,
            'person_count': person_count
        }

    def get_go_stop_status(self, road_objects):
        """보행자 검출 여부에 따른 GO/STOP 상태 반환"""
        person_count = sum(1 for obj in road_objects if obj['class_name'] == 'person')
        return "stop" if person_count > 0 else "go", person_count

# 전역 서비스 인스턴스
deeplab_service = DeepLabSegmentationServices()

def save_result_image(image, filename):
    """결과 이미지 저장"""
    try:
        result_path = RESULTS_DIR / filename
        success = cv2.imwrite(str(result_path), image)
        if success:
            log_with_time(f"이미지 저장 성공: {result_path}")
            return True
        else:
            log_with_time(f"이미지 저장 실패: {result_path}")
            return False
    except Exception as e:
        log_with_time(f"이미지 저장 중 오류: {e}")
        return False

@app.route('/segment_road', methods=['POST'])
def segment_road():
    """도로 세그멘테이션 API"""
    try:
        # 이미지 받기
        if 'image' in request.files:
            file = request.files['image']
            image_bytes = file.read()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        elif 'image_url' in request.form:
            url = request.form['image_url']
            response = requests.get(url)
            image_array = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            return jsonify({'error': '이미지가 필요합니다'}), 400
        
        if image is None:
            return jsonify({'error': '이미지를 읽을 수 없습니다'}), 400
        
        # 자율주행용 처리
        result = deeplab_service.process_image_for_autonomous_driving(image)
        
        if result is None:
            return jsonify({'error': '세그멘테이션 처리 실패'}), 500
        
        # GO/STOP 상태 결정
        go_stop_status, person_count = deeplab_service.get_go_stop_status(result['road_objects'])
        
        # 결과 이미지 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        vis_filename = f"deeplab_road_seg_{timestamp}.jpg"
        save_result_image(result['visualization'], vis_filename)
        
        # 응답 데이터 구성
        response_data = {
            'success': True,
            'status': go_stop_status,  # 'go' 또는 'stop'
            'person_count': person_count,
            'visualization_filename': vis_filename,
            'scene_analysis': result['scene_analysis'],
            'road_objects': result['road_objects'],
            'distance_info': result['distance_info'],
            'total_objects': len(result['road_objects'])
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'처리 중 오류 발생: {str(e)}'}), 500

@app.route('/api/road_segmentation', methods=['POST'])
def api_road_segmentation():
    global last_receive_time
    start_time = time.time()
    now = start_time
    
    # 수신 간격 계산
    if last_receive_time is not None:
        interval_ms = int((now - last_receive_time) * 1000)
        log_with_time(f"[api_road_segmentation] 이전 요청 대비 수신 간격: {interval_ms} ms")
    last_receive_time = now
    
    log_with_time("[api_road_segmentation] 요청 수신")
    try:
        log_with_time(f"[api_road_segmentation] request.files: {request.files}")
        log_with_time(f"[api_road_segmentation] request.form: {request.form}")
        
        # 이미지 받기
        if 'image' in request.files:
            log_with_time("[api_road_segmentation] 이미지 파일 수신")
            file = request.files['image']
            image_bytes = file.read()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        elif 'image_url' in request.form:
            log_with_time(f"[api_road_segmentation] 이미지 URL 수신: {request.form['image_url']}")
            url = request.form['image_url']
            response = requests.get(url)
            image_array = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            log_with_time("[api_road_segmentation] 이미지 파라미터 없음")
            return jsonify({'error': '이미지가 필요합니다'}), 400
        
        if image is None:
            log_with_time("[api_road_segmentation] 이미지를 읽을 수 없음")
            return jsonify({'error': '이미지를 읽을 수 없습니다'}), 400
        
        log_with_time("[api_road_segmentation] 세그멘테이션 수행 시작")
        # 세그멘테이션만 수행
        segmentation_map = deeplab_service.segment_image(image)
        
        if segmentation_map is None:
            log_with_time("[api_road_segmentation] 세그멘테이션 실패")
            return jsonify({'error': '세그멘테이션 실패'}), 500
        
        log_with_time("[api_road_segmentation] 도로 객체 추출")
        # 도로 객체 추출
        road_objects = deeplab_service.extract_road_objects(image, segmentation_map)
        
        log_with_time("[api_road_segmentation] 장면 분석")
        # 장면 분석
        scene_analysis = deeplab_service.analyze_road_scene(image, segmentation_map)
        
        log_with_time("[api_road_segmentation] GO/STOP 상태 결정")
        # GO/STOP 상태 결정
        go_stop_status, person_count = deeplab_service.get_go_stop_status(road_objects)
        
        # 시각화 생성 (바운딩 박스 포함)
        log_with_time("[api_road_segmentation] 시각화 생성")
        visualization, _ = deeplab_service.create_road_visualization_with_boxes(image, segmentation_map, road_objects)
        
        # 결과 이미지 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        vis_filename = f"deeplab_road_seg_{timestamp}.jpg"
        save_result_image(visualization, vis_filename)
        
        response_data = {
            'success': True,
            'status': go_stop_status,  # 'go' 또는 'stop'
            'person_count': person_count,
            'road_objects': road_objects,
            'scene_analysis': scene_analysis,
            'total_objects': len(road_objects),
            'visualization_filename': vis_filename if save_result_image(visualization, vis_filename) else None,
            'timestamp': timestamp
        }
        
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)
        log_with_time(f"[api_road_segmentation] 결과: {go_stop_status}, 사람 수: {person_count}명")
        log_with_time(f"[api_road_segmentation] 처리~송신까지 소요 시간: {elapsed_ms} ms")
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        log_with_time(f"[api_road_segmentation] EXCEPTION: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'처리 중 오류 발생: {str(e)}'}), 500

@app.route('/api/go_stop', methods=['POST'])
def api_go_stop():
    """GO/STOP 전용 API - 보행자 검출 여부만 반환"""
    try:
        # 이미지 받기
        if 'image' in request.files:
            file = request.files['image']
            image_bytes = file.read()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        elif 'image_url' in request.form:
            url = request.form['image_url']
            response = requests.get(url)
            image_array = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            return jsonify({'error': '이미지가 필요합니다'}), 400
        
        if image is None:
            return jsonify({'error': '이미지를 읽을 수 없습니다'}), 400
        
        # 세그멘테이션 수행
        segmentation_map = deeplab_service.segment_image(image)
        
        if segmentation_map is None:
            return jsonify({'error': '세그멘테이션 실패'}), 500
        
        # 도로 객체 추출
        road_objects = deeplab_service.extract_road_objects(image, segmentation_map)
        
        # GO/STOP 상태 결정
        go_stop_status, person_count = deeplab_service.get_go_stop_status(road_objects)
        
        # 시각화 (바운딩 박스 포함)
        visualization, _ = deeplab_service.create_road_visualization_with_boxes(image, segmentation_map, road_objects)
        
        # 결과 이미지 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        vis_filename = f"deeplab_go_stop_{timestamp}.jpg"
        save_result_image(visualization, vis_filename)
        
        response_data = {
            'status': go_stop_status,  # 'go' 또는 'stop'
            'person_count': person_count
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'처리 중 오류 발생: {str(e)}'}), 500

@app.route('/detect_person', methods=['POST'])
def detect_person():
    """기존 segmentation_services.py와 동일한 형식의 보행자 검출 API"""
    try:
        start_time = time.time()
        
        # 이미지 받기
        if 'image' in request.files:
            file = request.files['image']
            image_bytes = file.read()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        else:
            return jsonify({'error': '이미지가 필요합니다'}), 400
        
        if image is None:
            return jsonify({'error': '이미지를 읽을 수 없습니다'}), 400
        
        # 세그멘테이션 수행
        segmentation_map = deeplab_service.segment_image(image)
        
        if segmentation_map is None:
            return jsonify({'error': '세그멘테이션 실패'}), 500
        
        # 도로 객체 추출
        road_objects = deeplab_service.extract_road_objects(image, segmentation_map)
        
        # GO/STOP 상태 결정
        go_stop_status, person_count = deeplab_service.get_go_stop_status(road_objects)
        
        # 시각화 (바운딩 박스 포함)
        visualization, _ = deeplab_service.create_road_visualization_with_boxes(image, segmentation_map, road_objects)
        
        # 결과 이미지 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        result_filename = f"deeplab_person_detect_{timestamp}.jpg"
        save_result_image(visualization, result_filename)
        
        # 기존 형식과 동일한 응답
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)
        
        return jsonify({
            'status': go_stop_status,  # "go" 또는 "stop"
            'person_count': person_count
        })
        
    except Exception as e:
        return jsonify({'error': f'처리 중 오류 발생: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """헬스 체크"""
    return jsonify({
        'status': 'healthy',
        'service': 'DeepLabV3+ Road Segmentation',
        'device': str(deeplab_service.device)
    })

if __name__ == '__main__':
    print("🚀 DeepLabV3+ 도로 세그멘테이션 서버 시작...")
    print("📱 웹 인터페이스: http://localhost:5001")
    print("🔗 API 엔드포인트: http://localhost:5001/api/road_segmentation")
    app.run(debug=True, host='0.0.0.0', port=5001) 