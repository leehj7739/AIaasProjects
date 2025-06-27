#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 기반 이미지 세그멘테이션 서비스
다양한 세그멘테이션 후처리 서비스를 제공합니다.
"""

from flask import Flask, request, jsonify, render_template, send_file
from ultralytics import YOLO
import cv2
import numpy as np
import os
import base64
import json
import torch
import requests
from urllib.parse import urlparse
import mediapipe as mp
from PIL import Image, ImageFilter, ImageEnhance
from pathlib import Path
import imageio

# PyTorch 2.6 호환성 설정
torch.serialization.add_safe_globals(['ultralytics.nn.tasks.SegmentationModel'])

app = Flask(__name__)

# 모델 초기화
yolo_model = YOLO('yolov8n-seg.pt')
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# 폴더 생성
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def remove_duplicates(boxes, masks, confidences, classes, iou_threshold=0.5):
    """중복 객체 제거 (Non-Maximum Suppression) - 클래스별로 수행"""
    if len(boxes) == 0:
        return [], [], [], []
    
    # 클래스별로 그룹화
    class_groups = {}
    for i, (box, mask, conf, cls) in enumerate(zip(boxes, masks, confidences, classes)):
        if cls not in class_groups:
            class_groups[cls] = []
        class_groups[cls].append((i, box, mask, conf, cls))
    
    # 각 클래스별로 중복 제거
    keep_indices = []
    
    for class_name, group in class_groups.items():
        if len(group) == 1:
            # 클래스가 하나뿐이면 바로 추가
            keep_indices.append(group[0][0])
        else:
            # 같은 클래스 내에서 중복 제거
            group_boxes = [item[1] for item in group]
            group_confidences = [item[3] for item in group]
            group_indices = [item[0] for item in group]
            
            # 박스를 numpy 배열로 변환
            boxes_np = np.array(group_boxes)
            confidences_np = np.array(group_confidences)
            
            # 신뢰도 순으로 정렬
            sorted_indices = np.argsort(confidences_np)[::-1]
            
            class_keep_indices = []
            
            while len(sorted_indices) > 0:
                # 가장 높은 신뢰도를 가진 박스 선택
                current_index = sorted_indices[0]
                class_keep_indices.append(group_indices[current_index])
                
                if len(sorted_indices) == 1:
                    break
                
                # 현재 박스
                current_box = boxes_np[current_index]
                
                # 나머지 박스들과 IoU 계산
                remaining_indices = sorted_indices[1:]
                remaining_boxes = boxes_np[remaining_indices]
                
                # IoU 계산
                ious = calculate_iou(current_box, remaining_boxes)
                
                # IoU가 임계값보다 낮은 박스들만 유지
                low_iou_indices = np.where(ious < iou_threshold)[0]
                sorted_indices = remaining_indices[low_iou_indices]
            
            keep_indices.extend(class_keep_indices)
    
    # 결과 반환
    filtered_boxes = [boxes[i] for i in keep_indices]
    filtered_masks = [masks[i] for i in keep_indices] if masks else []
    filtered_confidences = [confidences[i] for i in keep_indices]
    filtered_classes = [classes[i] for i in keep_indices]
    
    return filtered_boxes, filtered_masks, filtered_confidences, filtered_classes

def calculate_iou(box1, boxes):
    """IoU (Intersection over Union) 계산"""
    # box1: [x1, y1, x2, y2]
    # boxes: [[x1, y1, x2, y2], ...]
    
    x1 = np.maximum(box1[0], boxes[:, 0])
    y1 = np.maximum(box1[1], boxes[:, 1])
    x2 = np.minimum(box1[2], boxes[:, 2])
    y2 = np.minimum(box1[3], boxes[:, 3])
    
    intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    
    union = area1 + area2 - intersection
    
    return intersection / (union + 1e-6)  # 0으로 나누기 방지

def process_detection_results(results, confidence_threshold=0.3, iou_threshold=0.5):
    """검출 결과를 처리하고 중복 제거"""
    all_boxes = []
    all_masks = []
    all_confidences = []
    all_classes = []
    
    for result in results:
        boxes = result.boxes
        masks = result.masks
        
        if boxes is not None:
            for i, box in enumerate(boxes):
                confidence = float(box.conf[0].cpu().numpy())
                
                # 신뢰도 임계값 확인
                if confidence < confidence_threshold:
                    continue
                
                cls = int(box.cls[0].cpu().numpy())
                class_name = result.names[cls]
                bbox = box.xyxy[0].cpu().numpy().tolist()
                
                all_boxes.append(bbox)
                all_confidences.append(confidence)
                all_classes.append(class_name)
                
                # 마스크 추가
                if masks is not None and i < len(masks.data):
                    mask_data = masks.data[i].cpu().numpy()
                    all_masks.append(mask_data)
                else:
                    all_masks.append(None)
    
    # 중복 제거
    filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = remove_duplicates(
        all_boxes, all_masks, all_confidences, all_classes, iou_threshold
    )
    
    return filtered_boxes, filtered_masks, filtered_confidences, filtered_classes

def download_image_from_url(url):
    """URL에서 이미지 다운로드"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        image_array = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("이미지를 디코딩할 수 없습니다")
        
        return image
    except Exception as e:
        raise Exception(f"이미지 다운로드 실패: {str(e)}")

def get_image_from_request():
    """요청에서 이미지 가져오기"""
    image = None
    is_gif = False
    gif_bytes = None
    
    # 파일 업로드 확인
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            image_bytes = file.read()
            
            # GIF 파일인지 확인
            if is_gif_image(image_bytes):
                is_gif = True
                gif_bytes = image_bytes
                # GIF의 첫 번째 프레임을 미리보기용으로 사용
                gif = imageio.mimread(gif_bytes, format='gif')
                if gif:
                    frame = gif[0]
                    if len(frame.shape) == 3 and frame.shape[2] == 4:  # RGBA
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:  # RGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    image = frame
            else:
                # 일반 이미지 처리
                image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    # URL 업로드 확인
    elif 'image_url' in request.form and request.form['image_url'].strip():
        url = request.form['image_url'].strip()
        if not url:
            raise ValueError('이미지 URL이 비어있습니다')
        
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError('유효하지 않은 URL입니다')
        
        # URL에서 이미지 다운로드
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        image_bytes = response.content
        
        # GIF 파일인지 확인
        if is_gif_image(image_bytes):
            is_gif = True
            gif_bytes = image_bytes
            # GIF의 첫 번째 프레임을 미리보기용으로 사용
            gif = imageio.mimread(gif_bytes, format='gif')
            if gif:
                frame = gif[0]
                if len(frame.shape) == 3 and frame.shape[2] == 4:  # RGBA
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                elif len(frame.shape) == 3 and frame.shape[2] == 3:  # RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                image = frame
        else:
            # 일반 이미지 처리
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    
    else:
        raise ValueError('이미지 파일 또는 URL이 필요합니다')
    
    if image is None:
        raise ValueError('이미지를 읽을 수 없습니다')
    
    return image, is_gif, gif_bytes

# 1. 배경 제거 서비스
@app.route('/service/remove_background', methods=['POST'])
def remove_background_service():
    """배경 제거 서비스"""
    try:
        print("🔍 배경 제거 서비스 시작...")
        image, is_gif, gif_bytes = get_image_from_request()
        print(f"이미지 로드 완료 - 크기: {image.shape if image is not None else 'None'}")
        
        target_class = request.form.get('target_class', 'person')
        iou_threshold = float(request.form.get('iou_threshold', 0.5))
        mask_precision = float(request.form.get('mask_precision', 0.3))
        print(f"설정값 - 대상: {target_class}, IoU: {iou_threshold}, 정밀도: {mask_precision}")
        
        # GIF 파일인 경우
        if is_gif and gif_bytes:
            print("GIF 파일 감지 - 프레임별 처리 시작")
            
            # GIF의 모든 프레임 처리
            processed_frames = process_gif_frames(
                gif_bytes, 
                target_class=target_class, 
                iou_threshold=iou_threshold, 
                mask_precision=mask_precision, 
                service_type='background_removal'
            )
            
            # 결과 GIF 저장
            result_filename = f"bg_removed_{target_class}_{len(os.listdir(RESULTS_FOLDER))}.gif"
            result_path = os.path.join(RESULTS_FOLDER, result_filename)
            
            # RGBA 프레임들을 RGB로 변환하여 GIF 저장
            rgb_frames = []
            for frame in processed_frames:
                if frame.shape[2] == 4:  # RGBA
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                else:  # BGR
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frames.append(rgb_frame)
            
            imageio.mimsave(result_path, rgb_frames, format='gif', duration=0.1, loop=0)
            print(f"GIF 결과 저장: {result_path}")
            
            # 첫 번째 프레임을 미리보기용으로 사용
            preview_frame = processed_frames[0]
            if preview_frame.shape[2] == 4:  # RGBA
                preview_frame = cv2.cvtColor(preview_frame, cv2.COLOR_BGRA2BGR)
            
            # base64 인코딩 (미리보기용)
            _, buffer = cv2.imencode('.jpg', preview_frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return jsonify({
                'success': True,
                'result_image': img_base64,
                'filename': result_filename,
                'service': 'remove_background',
                'is_gif': True,
                'frame_count': len(processed_frames),
                'duplicates_removed': True,
                'iou_threshold': iou_threshold,
                'target_class': target_class
            })
        
        # 일반 이미지 처리 (기존 코드)
        print("일반 이미지 처리 시작...")
        # 객체 감지
        results = yolo_model(image)
        print(f"YOLO 모델 실행 완료 - 결과 수: {len(results)}")
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=iou_threshold
        )
        print(f"중복 제거 완료 - 검출된 객체: {len(filtered_boxes)}개")
        
        # 마스크 생성
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        extracted_objects = []
        
        for i, (bbox, mask_data, confidence, class_name) in enumerate(zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes)):
            print(f"객체 {i+1}: {class_name} (신뢰도: {confidence:.2f}, 마스크: {'있음' if mask_data is not None else '없음'})")
            # 모든 객체 선택 또는 특정 클래스 선택
            if (target_class == 'all' or class_name == target_class) and mask_data is not None:
                print(f"  -> {class_name} 객체 처리 중...")
                # 정밀한 마스크 생성
                object_mask = create_precise_mask(
                    mask_data, 
                    image.shape, 
                    threshold=mask_precision,  # 사용자 설정 정밀도 사용
                    refine=True     # 마스크 정밀도 향상 적용
                )
                mask = np.maximum(mask, object_mask)
                
                # bbox가 numpy 배열인지 리스트인지 확인
                if hasattr(bbox, 'tolist'):
                    bbox_list = bbox.tolist()
                else:
                    bbox_list = bbox
                
                extracted_objects.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox_list
                })
        
        print(f"추출된 객체 수: {len(extracted_objects)}개")
        
        if len(extracted_objects) == 0:
            return jsonify({'error': f'선택한 대상 객체({target_class})를 찾을 수 없습니다'}), 400
        
        # 배경 제거
        print("배경 제거 처리 중...")
        # 1. 마스크를 3채널로 확장 (데이터 타입 주의)
        mask_normalized = mask.astype(np.float32) / 255.0
        mask_3d = np.stack([mask_normalized] * 3, axis=2)
        
        # 2. 객체만 추출
        result_image = image * mask_3d
        
        # 3. 투명 배경을 위해 RGBA로 변환
        rgba_image = cv2.cvtColor(result_image, cv2.COLOR_BGR2BGRA)
        rgba_image[:, :, 3] = mask  # 알파 채널 설정
        
        # 결과 저장 (PNG로 저장하여 투명도 유지)
        result_filename = f"bg_removed_{target_class}_{len(os.listdir(RESULTS_FOLDER))}.png"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        cv2.imwrite(result_path, rgba_image)
        print(f"결과 저장 완료: {result_path}")
        
        # 웹 표시용으로는 BGR 이미지 사용
        _, buffer = cv2.imencode('.jpg', result_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print("✅ 배경 제거 서비스 완료!")
        return jsonify({
            'success': True,
            'result_image': img_base64,
            'filename': result_filename,
            'service': 'remove_background',
            'detected_objects': len(filtered_boxes),
            'extracted_objects': extracted_objects,
            'duplicates_removed': True,
            'iou_threshold': iou_threshold,
            'target_class': target_class
        })
        
    except Exception as e:
        print(f"❌ 배경 제거 서비스 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 2. 객체 추출 서비스
@app.route('/service/extract_objects', methods=['POST'])
def extract_objects_service():
    """객체 추출 서비스"""
    try:
        image, is_gif, gif_bytes = get_image_from_request()
        target_classes = request.form.get('target_classes', '').split(',')
        if target_classes == ['']:
            target_classes = None
        
        # 객체 감지
        results = yolo_model(image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=0.5
        )
        
        extracted_objects = []
        
        for i, (bbox, mask_data, confidence, class_name) in enumerate(zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes)):
            if target_classes is None or class_name in target_classes:
                if mask_data is not None:
                    # 정밀한 마스크 생성
                    object_mask = create_precise_mask(
                        mask_data, 
                        image.shape, 
                        threshold=0.3,  # 더 낮은 임계값으로 더 많은 픽셀 포함
                        refine=True     # 마스크 정밀도 향상 적용
                    )
                    
                    # 마스크를 불린 배열로 변환
                    mask_bool = object_mask > 0
                    
                    # 객체 추출
                    extracted = image.copy()
                    extracted[~mask_bool] = [255, 255, 255]
                    
                    # 개별 객체 저장
                    obj_filename = f"extracted_{class_name}_{len(extracted_objects)}.png"
                    obj_path = os.path.join(RESULTS_FOLDER, obj_filename)
                    cv2.imwrite(obj_path, extracted)
                    
                    extracted_objects.append({
                        'class': class_name,
                        'filename': obj_filename,
                        'bbox': bbox,
                        'confidence': confidence
                    })
        
        return jsonify({
            'success': True,
            'extracted_objects': extracted_objects,
            'total_objects': len(extracted_objects),
            'service': 'object_extraction',
            'duplicates_removed': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. 얼굴 뷰티 서비스
@app.route('/service/face_beauty', methods=['POST'])
def face_beauty_service():
    """얼굴 뷰티 서비스"""
    try:
        image, is_gif, gif_bytes = get_image_from_request()
        
        # 얼굴 랜드마크 검출
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_image)
        
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
        
        # 결과 저장
        result_filename = f"beauty_{len(os.listdir(RESULTS_FOLDER))}.jpg"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        cv2.imwrite(result_path, result_image)
        
        # base64 인코딩
        _, buffer = cv2.imencode('.jpg', result_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'result_image': img_base64,
            'filename': result_filename,
            'service': 'face_beauty'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 4. 객체 카운팅 서비스
@app.route('/service/count_objects', methods=['POST'])
def count_objects_service():
    """객체 카운팅 서비스"""
    try:
        image, is_gif, gif_bytes = get_image_from_request()
        target_classes = request.form.get('target_classes', '').split(',')
        if target_classes == ['']:
            target_classes = None
        
        # 객체 감지
        results = yolo_model(image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=0.5
        )
        
        object_counts = {}
        object_details = []
        
        for bbox, confidence, class_name in zip(filtered_boxes, filtered_confidences, filtered_classes):
            if target_classes is None or class_name in target_classes:
                object_counts[class_name] = object_counts.get(class_name, 0) + 1
                object_details.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox
                })
        
        return jsonify({
            'success': True,
            'object_counts': object_counts,
            'object_details': object_details,
            'total_objects': sum(object_counts.values()),
            'service': 'object_counting',
            'duplicates_removed': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 5. 이미지 분석 서비스
@app.route('/service/analyze_image', methods=['POST'])
def analyze_image_service():
    """이미지 종합 분석 서비스"""
    try:
        image, is_gif, gif_bytes = get_image_from_request()
        
        # 객체 감지
        results = yolo_model(image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=0.5
        )
        
        analysis = {
            'objects': [],
            'total_objects': 0,
            'image_size': image.shape,
            'dominant_objects': [],
            'object_counts': {}
        }
        
        object_counts = {}
        
        for i, (bbox, mask_data, confidence, class_name) in enumerate(zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes)):
            # 객체 정보
            obj_info = {
                'class': class_name,
                'confidence': confidence,
                'bbox': bbox,
                'area': (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            }
            
            # 마스크 정보 추가
            if mask_data is not None:
                mask_resized = cv2.resize(mask_data, (image.shape[1], image.shape[0]))
                mask_area = np.sum(mask_resized > 0.5)
                obj_info['mask_area'] = int(mask_area)
            
            analysis['objects'].append(obj_info)
            object_counts[class_name] = object_counts.get(class_name, 0) + 1
        
        analysis['total_objects'] = len(analysis['objects'])
        analysis['object_counts'] = object_counts
        
        # 주요 객체 찾기 (면적 기준)
        if analysis['objects']:
            sorted_objects = sorted(analysis['objects'], key=lambda x: x.get('mask_area', 0), reverse=True)
            analysis['dominant_objects'] = [obj['class'] for obj in sorted_objects[:3]]
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'service': 'image_analysis',
            'duplicates_removed': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 6. 이미지 필터 서비스
@app.route('/service/apply_filter', methods=['POST'])
def apply_filter_service():
    """이미지 필터 적용 서비스"""
    try:
        image, is_gif, gif_bytes = get_image_from_request()
        filter_type = request.form.get('filter_type', 'blur')
        target_class = request.form.get('target_class', 'person')
        
        # 객체 감지
        results = yolo_model(image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=0.5
        )
        
        result_image = image.copy()
        
        for i, (bbox, mask_data, confidence, class_name) in enumerate(zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes)):
            if class_name == target_class and mask_data is not None:
                # 정밀한 마스크 생성
                object_mask = create_precise_mask(
                    mask_data, 
                    image.shape, 
                    threshold=0.3,  # 더 낮은 임계값으로 더 많은 픽셀 포함
                    refine=True     # 마스크 정밀도 향상 적용
                )
                
                # 마스크를 불린 배열로 변환
                mask_bool = object_mask > 0
                
                # 필터 적용
                if filter_type == 'blur':
                    blurred = cv2.GaussianBlur(result_image, (15, 15), 0)
                    result_image[mask_bool] = blurred[mask_bool]
                elif filter_type == 'brightness':
                    hsv = cv2.cvtColor(result_image, cv2.COLOR_BGR2HSV)
                    hsv[mask_bool, 2] = np.clip(hsv[mask_bool, 2] * 1.5, 0, 255)
                    result_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                elif filter_type == 'contrast':
                    lab = cv2.cvtColor(result_image, cv2.COLOR_BGR2LAB)
                    lab[mask_bool, 0] = np.clip(lab[mask_bool, 0] * 1.3, 0, 255)
                    result_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 결과 저장
        result_filename = f"filtered_{filter_type}_{len(os.listdir(RESULTS_FOLDER))}.jpg"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        cv2.imwrite(result_path, result_image)
        
        # base64 인코딩
        _, buffer = cv2.imencode('.jpg', result_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'result_image': img_base64,
            'filename': result_filename,
            'filter_type': filter_type,
            'service': 'image_filter',
            'duplicates_removed': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 검출된 객체 목록 반환
@app.route('/service/get_detected_objects', methods=['POST'])
def get_detected_objects_service():
    """검출된 객체 목록 반환"""
    try:
        image, is_gif, gif_bytes = get_image_from_request()
        iou_threshold = float(request.form.get('iou_threshold', 0.5))
        
        # 객체 감지
        results = yolo_model(image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=iou_threshold
        )
        
        # 검출된 객체들의 고유한 클래스 목록
        unique_classes = list(set(filtered_classes))
        
        return jsonify({
            'success': True,
            'detected_classes': unique_classes,
            'total_objects': len(filtered_classes),
            'object_counts': {cls: filtered_classes.count(cls) for cls in unique_classes}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 배경 합성 서비스
@app.route('/service/background_composition', methods=['POST'])
def background_composition_service():
    """배경 합성 서비스"""
    try:
        print("배경 합성 서비스 시작")
        print(f"요청 파일: {list(request.files.keys())}")
        print(f"요청 폼 데이터: {list(request.form.keys())}")
        
        # 원본 이미지 가져오기
        original_image, is_gif, gif_bytes = get_image_from_request()
        print(f"원본 이미지 크기: {original_image.shape}")
        
        target_class = request.form.get('target_class', 'person')
        iou_threshold = float(request.form.get('iou_threshold', 0.5))
        mask_precision = float(request.form.get('mask_precision', 0.3))
        print(f"대상 클래스: {target_class}, IoU 임계값: {iou_threshold}")
        
        # 새 배경 이미지 가져오기
        background_image = None
        background_gif_frames = None
        
        # 새 배경 파일 업로드 확인
        if 'background_image' in request.files:
            file = request.files['background_image']
            if file.filename != '':
                print(f"배경 이미지 파일: {file.filename}")
                image_bytes = file.read()
                if is_gif_image(image_bytes):
                    print("배경 이미지가 GIF입니다.")
                    import imageio
                    background_gif_frames = imageio.mimread(image_bytes, format='gif')
                    print(f"배경 GIF 프레임 수: {len(background_gif_frames)}")
                    # 첫 프레임을 미리보기용으로 사용
                    background_image = background_gif_frames[0]
                    if len(background_image.shape) == 3 and background_image.shape[2] == 4:
                        background_image = cv2.cvtColor(background_image, cv2.COLOR_RGBA2BGR)
                    elif len(background_image.shape) == 3 and background_image.shape[2] == 3:
                        background_image = cv2.cvtColor(background_image, cv2.COLOR_RGB2BGR)
                else:
                    background_image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                    print(f"배경 이미지 크기: {background_image.shape if background_image is not None else 'None'}")
        
        # 새 배경 URL 확인
        elif 'background_url' in request.form and request.form['background_url'].strip():
            url = request.form['background_url'].strip()
            print(f"배경 이미지 URL: {url}")
            if url:
                parsed_url = urlparse(url)
                if parsed_url.scheme and parsed_url.netloc:
                    background_image = download_image_from_url(url)
                    print(f"배경 이미지 크기: {background_image.shape if background_image is not None else 'None'}")
        
        if background_image is None:
            return jsonify({'error': '새 배경 이미지가 필요합니다'}), 400
        
        # GIF 파일인 경우
        if is_gif and gif_bytes:
            print("GIF 파일 감지 - 프레임별 배경 합성 시작")
            import imageio
            # 메인 GIF 프레임 추출
            main_gif_frames = imageio.mimread(gif_bytes, format='gif')
            main_frame_count = len(main_gif_frames)
            print(f"메인 GIF 프레임 수: {main_frame_count}")
            # 배경 프레임 준비
            if background_gif_frames is not None:
                bg_frame_count = len(background_gif_frames)
                # 배경 프레임을 메인 프레임 수에 맞게 반복 또는 자름
                if bg_frame_count < main_frame_count:
                    repeat = (main_frame_count + bg_frame_count - 1) // bg_frame_count
                    background_gif_frames = (background_gif_frames * repeat)[:main_frame_count]
                elif bg_frame_count > main_frame_count:
                    background_gif_frames = background_gif_frames[:main_frame_count]
            else:
                # 단일 배경 이미지를 모든 프레임에 사용
                background_gif_frames = [background_image] * main_frame_count
            processed_frames = []
            for i, (main_frame, bg_frame) in enumerate(zip(main_gif_frames, background_gif_frames)):
                print(f"프레임 {i+1}/{main_frame_count} 합성 중...")
                # 프레임 색상 변환
                if len(main_frame.shape) == 3 and main_frame.shape[2] == 4:
                    main_frame_bgr = cv2.cvtColor(main_frame, cv2.COLOR_RGBA2BGR)
                elif len(main_frame.shape) == 3 and main_frame.shape[2] == 3:
                    main_frame_bgr = cv2.cvtColor(main_frame, cv2.COLOR_RGB2BGR)
                else:
                    main_frame_bgr = main_frame
                if len(bg_frame.shape) == 3 and bg_frame.shape[2] == 4:
                    bg_bgr = cv2.cvtColor(bg_frame, cv2.COLOR_RGBA2BGR)
                elif len(bg_frame.shape) == 3 and bg_frame.shape[2] == 3:
                    bg_bgr = cv2.cvtColor(bg_frame, cv2.COLOR_RGB2BGR)
                else:
                    bg_bgr = bg_frame
                # 배경 리사이즈
                bg_bgr = cv2.resize(bg_bgr, (main_frame_bgr.shape[1], main_frame_bgr.shape[0]))
                # 객체 감지 및 마스크 생성
                results = yolo_model(main_frame_bgr)
                filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
                    results, confidence_threshold=0.3, iou_threshold=iou_threshold
                )
                mask = np.zeros(main_frame_bgr.shape[:2], dtype=np.uint8)
                for bbox, mask_data, confidence, class_name in zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes):
                    if (target_class == 'all' or class_name == target_class) and mask_data is not None:
                        object_mask = create_precise_mask(
                            mask_data, 
                            main_frame_bgr.shape, 
                            threshold=mask_precision, 
                            refine=True
                        )
                        mask = np.maximum(mask, object_mask)
                mask_normalized = mask.astype(np.float32) / 255.0
                mask_3d = np.stack([mask_normalized] * 3, axis=2)
                result_frame = main_frame_bgr * mask_3d + bg_bgr * (1 - mask_3d)
                result_frame = result_frame.astype(np.uint8)
                processed_frames.append(result_frame)
            # 결과 GIF 저장
            result_filename = f"composed_{target_class}_{len(os.listdir(RESULTS_FOLDER))}.gif"
            result_path = os.path.join(RESULTS_FOLDER, result_filename)
            rgb_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in processed_frames]
            imageio.mimsave(result_path, rgb_frames, format='gif', duration=0.1, loop=0)
            print(f"GIF 결과 저장: {result_path}")
            preview_frame = processed_frames[0]
            _, buffer = cv2.imencode('.jpg', preview_frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return jsonify({
                'success': True,
                'result_image': img_base64,
                'filename': result_filename,
                'service': 'background_composition',
                'is_gif': True,
                'frame_count': len(processed_frames),
                'duplicates_removed': True,
                'iou_threshold': iou_threshold,
                'target_class': target_class
            })
        
        # 일반 이미지 처리 (기존 코드)
        # 객체 감지
        print("객체 감지 시작")
        results = yolo_model(original_image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=iou_threshold
        )
        print(f"검출된 객체: {filtered_classes}")
        
        # 마스크 생성
        mask = np.zeros(original_image.shape[:2], dtype=np.uint8)
        composed_objects = []
        
        for i, (bbox, mask_data, confidence, class_name) in enumerate(zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes)):
            # 모든 객체 선택 또는 특정 클래스 선택
            if (target_class == 'all' or class_name == target_class) and mask_data is not None:
                # 정밀한 마스크 생성
                object_mask = create_precise_mask(
                    mask_data, 
                    original_image.shape, 
                    threshold=mask_precision,  # 사용자 설정 정밀도 사용
                    refine=True     # 마스크 정밀도 향상 적용
                )
                mask = np.maximum(mask, object_mask)
                
                # bbox가 numpy 배열인지 리스트인지 확인
                if hasattr(bbox, 'tolist'):
                    bbox_list = bbox.tolist()
                else:
                    bbox_list = bbox
                
                composed_objects.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox_list
                })
                print(f"{class_name} 객체 {i+1}: 신뢰도 {confidence:.2f}")
        
        print(f"합성할 객체 수: {len(composed_objects)}")
        
        if len(composed_objects) == 0:
            return jsonify({'error': f'선택한 대상 객체({target_class})를 찾을 수 없습니다'}), 400
        
        # 배경 합성
        print("배경 합성 시작")
        # 1. 새 배경을 원본 이미지 크기로 리사이즈
        background_resized = cv2.resize(background_image, (original_image.shape[1], original_image.shape[0]))
        
        # 2. 마스크를 3채널로 확장 (데이터 타입 주의)
        mask_normalized = mask.astype(np.float32) / 255.0
        mask_3d = np.stack([mask_normalized] * 3, axis=2)
        
        # 3. 객체와 배경 합성
        result_image = original_image * mask_3d + background_resized * (1 - mask_3d)
        result_image = result_image.astype(np.uint8)
        
        # 결과 저장
        result_filename = f"composed_{target_class}_{len(os.listdir(RESULTS_FOLDER))}.jpg"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        cv2.imwrite(result_path, result_image)
        print(f"결과 저장: {result_path}")
        
        # base64 인코딩
        _, buffer = cv2.imencode('.jpg', result_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print("배경 합성 서비스 완료")
        return jsonify({
            'success': True,
            'result_image': img_base64,
            'filename': result_filename,
            'service': 'background_composition',
            'detected_objects': len(filtered_boxes),
            'composed_objects': composed_objects,
            'duplicates_removed': True,
            'iou_threshold': iou_threshold,
            'target_class': target_class
        })
        
    except ValueError as ve:
        print(f"배경 합성 서비스 ValueError: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"배경 합성 서비스 예외: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def demo_background_composition():
    """배경 합성 데모"""
    print("\n🎭 배경 합성 데모")
    print("=" * 50)
    
    # 샘플 이미지 URL (여러 객체가 있는 이미지)
    sample_image_url = "https://images.unsplash.com/photo-1543852786-1cf6624b9987?w=400"
    
    # 배경 이미지 URL (자연 풍경)
    background_url = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
    
    print(f"원본 이미지: {sample_image_url}")
    print(f"새 배경: {background_url}")
    
    try:
        # 원본 이미지 다운로드
        original_image = download_image_from_url(sample_image_url)
        if original_image is None:
            print("❌ 원본 이미지 다운로드 실패")
            return
        
        # 배경 이미지 다운로드
        background_image = download_image_from_url(background_url)
        if background_image is None:
            print("❌ 배경 이미지 다운로드 실패")
            return
        
        print("✅ 이미지 다운로드 완료")
        
        # 객체 감지
        results = yolo_model(original_image)
        
        # 중복 제거된 결과 처리
        filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
            results, confidence_threshold=0.3, iou_threshold=0.5
        )
        
        print(f"검출된 객체: {filtered_classes}")
        
        # 모든 객체 마스크 생성
        mask = np.zeros(original_image.shape[:2], dtype=np.uint8)
        composed_objects = []
        
        for i, (bbox, mask_data, confidence, class_name) in enumerate(zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes)):
            if mask_data is not None:
                # 정밀한 마스크 생성
                object_mask = create_precise_mask(
                    mask_data, 
                    original_image.shape, 
                    threshold=0.3,  # 더 낮은 임계값으로 더 많은 픽셀 포함
                    refine=True     # 마스크 정밀도 향상 적용
                )
                mask = np.maximum(mask, object_mask)
                
                # bbox가 numpy 배열인지 리스트인지 확인
                if hasattr(bbox, 'tolist'):
                    bbox_list = bbox.tolist()
                else:
                    bbox_list = bbox
                
                composed_objects.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox_list
                })
                print(f"{class_name} 객체 {i+1}: 신뢰도 {confidence:.2f}")
        
        if len(composed_objects) == 0:
            print("❌ 검출된 객체가 없습니다")
            return
        
        print(f"합성할 객체 수: {len(composed_objects)}개")
        
        # 배경 합성
        # 1. 새 배경을 원본 이미지 크기로 리사이즈
        background_resized = cv2.resize(background_image, (original_image.shape[1], original_image.shape[0]))
        
        # 2. 마스크를 3채널로 확장 (데이터 타입 주의)
        mask_normalized = mask.astype(np.float32) / 255.0
        mask_3d = np.stack([mask_normalized] * 3, axis=2)
        
        # 3. 객체와 배경 합성
        result_image = original_image * mask_3d + background_resized * (1 - mask_3d)
        result_image = result_image.astype(np.uint8)
        
        # 결과 저장
        result_filename = f"composed_all_{len(os.listdir(RESULTS_FOLDER))}.jpg"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        cv2.imwrite(result_path, result_image)
        
        print(f"✅ 배경 합성 완료: {result_filename}")
        print(f"저장 위치: {result_path}")
        
        # 결과 이미지 크기 정보
        print(f"원본 크기: {original_image.shape[1]}x{original_image.shape[0]}")
        print(f"배경 크기: {background_image.shape[1]}x{background_image.shape[0]}")
        print(f"결과 크기: {result_image.shape[1]}x{result_image.shape[0]}")
        
        # 합성된 객체 정보
        print(f"합성된 객체: {[obj['class'] for obj in composed_objects]}")
        
    except Exception as e:
        print(f"❌ 배경 합성 실패: {str(e)}")

def refine_mask(mask, kernel_size=3, iterations=1):
    """마스크 정밀도 향상을 위한 후처리"""
    # 모폴로지 연산으로 노이즈 제거
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    # 열기 연산 (erosion + dilation) - 작은 노이즈 제거
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
    
    # 닫기 연산 (dilation + erosion) - 작은 구멍 메우기
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    
    return mask

def create_precise_mask(mask_data, target_shape, threshold=0.3, refine=True):
    """정밀한 마스크 생성"""
    # mask_data가 None인 경우 빈 마스크 반환
    if mask_data is None:
        return np.zeros(target_shape[:2], dtype=np.uint8)
    
    # 마스크 리사이즈
    mask_resized = cv2.resize(mask_data, (target_shape[1], target_shape[0]))
    
    # 데이터 타입을 float32로 변환 (OpenCV 호환성)
    mask_resized = mask_resized.astype(np.float32)
    
    # 더 낮은 임계값으로 마스크 생성 (더 많은 픽셀 포함)
    mask = (mask_resized > threshold).astype(np.uint8) * 255
    
    if refine:
        # 마스크 정밀도 향상
        mask = refine_mask(mask, kernel_size=3, iterations=1)
    
    return mask

# 메인 페이지
@app.route('/')
def index():
    """서비스 메인 페이지"""
    return render_template('services.html')

# 결과 파일 다운로드
@app.route('/download/<filename>')
def download_result(filename):
    """결과 파일 다운로드"""
    try:
        return send_file(os.path.join(RESULTS_FOLDER, filename), as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

def is_gif_image(image_bytes):
    """이미지가 GIF인지 확인"""
    try:
        # 첫 번째 바이트로 GIF 시그니처 확인
        return image_bytes[:4] == b'GIF8'
    except:
        return False

def process_gif_frames(gif_bytes, target_class='all', iou_threshold=0.5, mask_precision=0.3, service_type='background_removal'):
    """GIF의 각 프레임을 처리"""
    try:
        # GIF 읽기
        gif = imageio.mimread(gif_bytes, format='gif')
        
        if not gif:
            raise ValueError("GIF를 읽을 수 없습니다")
        
        print(f"GIF 프레임 수: {len(gif)}")
        
        processed_frames = []
        
        for i, frame in enumerate(gif):
            print(f"프레임 {i+1}/{len(gif)} 처리 중...")
            
            # PIL Image를 OpenCV 형식으로 변환
            if len(frame.shape) == 3 and frame.shape[2] == 4:  # RGBA
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            elif len(frame.shape) == 3 and frame.shape[2] == 3:  # RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # 객체 감지
            results = yolo_model(frame)
            
            # 중복 제거된 결과 처리
            filtered_boxes, filtered_masks, filtered_confidences, filtered_classes = process_detection_results(
                results, confidence_threshold=0.3, iou_threshold=iou_threshold
            )
            
            # 마스크 생성
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            
            for bbox, mask_data, confidence, class_name in zip(filtered_boxes, filtered_masks, filtered_confidences, filtered_classes):
                if (target_class == 'all' or class_name == target_class) and mask_data is not None:
                    object_mask = create_precise_mask(
                        mask_data, 
                        frame.shape, 
                        threshold=mask_precision,
                        refine=True
                    )
                    mask = np.maximum(mask, object_mask)
            
            # 서비스별 처리
            if service_type == 'background_removal':
                # 배경 제거
                mask_normalized = mask.astype(np.float32) / 255.0
                mask_3d = np.stack([mask_normalized] * 3, axis=2)
                processed_frame = frame * mask_3d
                
                # 데이터 타입을 uint8로 변환 (OpenCV 호환성)
                processed_frame = processed_frame.astype(np.uint8)
                
                # RGBA로 변환 (투명 배경)
                rgba_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2BGRA)
                rgba_frame[:, :, 3] = mask
                processed_frames.append(rgba_frame)
                
            elif service_type == 'background_composition':
                # 배경 합성 (첫 번째 프레임의 배경 사용)
                if i == 0:
                    # 첫 번째 프레임은 원본 배경 사용
                    processed_frames.append(frame)
                else:
                    # 나머지 프레임은 첫 번째 프레임을 배경으로 사용
                    background = processed_frames[0]
                    mask_normalized = mask.astype(np.float32) / 255.0
                    mask_3d = np.stack([mask_normalized] * 3, axis=2)
                    processed_frame = frame * mask_3d + background * (1 - mask_3d)
                    processed_frame = processed_frame.astype(np.uint8)
                    processed_frames.append(processed_frame)
        
        return processed_frames
        
    except Exception as e:
        print(f"GIF 처리 중 오류: {str(e)}")
        raise e

if __name__ == '__main__':
    print("🚀 이미지 세그멘테이션 서비스 서버 시작...")
    print("📱 웹 인터페이스: http://localhost:5000")
    print("🔗 서비스 엔드포인트:")
    print("  - 배경 제거: /service/remove_background")
    print("  - 배경 합성: /service/background_composition")
    print("  - 객체 추출: /service/extract_objects")
    print("  - 얼굴 뷰티: /service/face_beauty")
    print("  - 객체 카운팅: /service/count_objects")
    print("  - 이미지 분석: /service/analyze_image")
    print("  - 이미지 필터: /service/apply_filter")
    print("  - 검출된 객체 목록: /service/get_detected_objects")
    
    # 데모 실행 (선택사항)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        print("\n🎬 데모 모드 실행...")
        demo_background_composition()
        print("\n✅ 데모 완료!")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 