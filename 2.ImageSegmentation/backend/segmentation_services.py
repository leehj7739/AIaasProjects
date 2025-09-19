#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 세그멘테이션 후 제공할 수 있는 서비스들
"""

import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
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

app = Flask(__name__)


class SegmentationServices:
    def __init__(self):
        """세그멘테이션 서비스 초기화"""
        self.yolo_model = YOLO('yolov8n-seg.pt')
        
        # MediaPipe 얼굴 랜드마크
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

    def detect_objects(self, image):
        """객체 감지 및 세그멘테이션"""
        results = self.yolo_model(image)
        return results

    def detect_face_landmarks(self, image):
        """얼굴 랜드마크 검출"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        return results

    # 1. 배경 제거/교체 서비스
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

    def replace_background(self, image, new_background_path, target_class='person'):
        """배경 교체"""
        # 배경 제거
        result_image, mask = self.remove_background(image, target_class)
        
        # 새 배경 로드
        new_bg = cv2.imread(new_background_path)
        if new_bg is not None:
            new_bg = cv2.resize(new_bg, (image.shape[1], image.shape[0]))
            
            # 마스크를 사용하여 배경 교체
            mask_3d = np.stack([mask/255.0] * 3, axis=2)
            result_image = image * mask_3d + new_bg * (1 - mask_3d)
        
        return result_image.astype(np.uint8)

    # 2. 객체 추출 및 분리 서비스
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

    # 3. 이미지 편집 서비스
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

    # 4. 얼굴 뷰티 서비스
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

    # 5. 객체 카운팅 서비스
    def count_objects(self, image, target_classes=None, draw_on_image=True):
        """객체 개수 세기"""
        results = self.detect_objects(image)
        object_counts = {}
        result_image = image.copy() if draw_on_image else None
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    
                    if target_classes is None or class_name in target_classes:
                        object_counts[class_name] = object_counts.get(class_name, 0) + 1
                        
                        # 이미지에 바운딩 박스 그리기
                        if draw_on_image:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            color = (0, 255, 0) if class_name == 'person' else (255, 0, 0)
                            label = f"{class_name} {conf:.2f}"
                            
                            cv2.rectangle(result_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                            cv2.putText(result_image, label, (int(x1), int(y1)-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # 사람 감지 개수를 좌하단에 표시
        if draw_on_image and 'person' in object_counts:
            person_count = object_counts['person']
            h, w = result_image.shape[:2]
            
            # 사람 감지 개수 텍스트 (영어)
            text = f'People: {person_count}'
            
            # 텍스트 크기 계산
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.0
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            
            # 좌하단 위치 계산 (여백 20픽셀)
            text_x = 20
            text_y = h - 20
            
            # 배경 사각형 그리기
            cv2.rectangle(result_image, 
                         (text_x - 10, text_y - text_height - 10),
                         (text_x + text_width + 10, text_y + 10),
                         (0, 0, 0), -1)
            
            # 텍스트 그리기
            cv2.putText(result_image, text, (text_x, text_y), 
                       font, font_scale, (255, 255, 255), thickness)
        
        return object_counts, result_image if draw_on_image else object_counts

    # 6. 이미지 분석 서비스
    def analyze_image(self, image):
        """이미지 종합 분석"""
        results = self.detect_objects(image)
        analysis = {
            'objects': [],
            'total_objects': 0,
            'image_size': image.shape,
            'dominant_objects': []
        }
        
        object_counts = {}
        
        for result in results:
            boxes = result.boxes
            masks = result.masks
            
            if boxes is not None:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    conf = float(box.conf[0].cpu().numpy())
                    bbox = box.xyxy[0].cpu().numpy().tolist()
                    
                    # 객체 정보
                    obj_info = {
                        'class': class_name,
                        'confidence': conf,
                        'bbox': bbox,
                        'area': (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    }
                    
                    # 마스크 정보 추가
                    if masks is not None and i < len(masks.data):
                        mask_data = masks.data[i].cpu().numpy()
                        mask_resized = cv2.resize(mask_data, (image.shape[1], image.shape[0]))
                        mask_area = np.sum(mask_resized > 0.5)
                        obj_info['mask_area'] = mask_area
                    
                    analysis['objects'].append(obj_info)
                    object_counts[class_name] = object_counts.get(class_name, 0) + 1
        
        analysis['total_objects'] = len(analysis['objects'])
        analysis['object_counts'] = object_counts
        
        # 주요 객체 찾기 (면적 기준)
        if analysis['objects']:
            sorted_objects = sorted(analysis['objects'], key=lambda x: x.get('mask_area', 0), reverse=True)
            analysis['dominant_objects'] = [obj['class'] for obj in sorted_objects[:3]]
        
        return analysis

    # 7. 이미지 생성 서비스
    def create_collage(self, image, layout='grid'):
        """객체들을 이용한 콜라주 생성"""
        extracted_objects = self.extract_objects(image)
        
        if not extracted_objects:
            return image
        
        # 콜라주 크기 계산
        n_objects = len(extracted_objects)
        if layout == 'grid':
            cols = int(np.ceil(np.sqrt(n_objects)))
            rows = int(np.ceil(n_objects / cols))
        else:
            cols = n_objects
            rows = 1
        
        # 콜라주 이미지 생성
        cell_size = 200
        collage = np.ones((rows * cell_size, cols * cell_size, 3), dtype=np.uint8) * 255
        
        for i, obj in enumerate(extracted_objects):
            row = i // cols
            col = i % cols
            
            # 객체 이미지 리사이즈
            obj_img = cv2.resize(obj['image'], (cell_size, cell_size))
            collage[row*cell_size:(row+1)*cell_size, col*cell_size:(col+1)*cell_size] = obj_img
        
        return collage

    # 8. 데이터 추출 서비스
    def extract_metadata(self, image):
        """이미지에서 메타데이터 추출"""
        analysis = self.analyze_image(image)
        
        metadata = {
            'filename': 'image.jpg',
            'size': f"{analysis['image_size'][1]}x{analysis['image_size'][0]}",
            'objects_detected': analysis['total_objects'],
            'object_types': list(analysis['object_counts'].keys()),
            'dominant_objects': analysis['dominant_objects'],
            'object_details': []
        }
        
        for obj in analysis['objects']:
            metadata['object_details'].append({
                'type': obj['class'],
                'confidence': f"{obj['confidence']:.2f}",
                'position': f"({obj['bbox'][0]:.0f}, {obj['bbox'][1]:.0f})",
                'size': f"{obj['bbox'][2]-obj['bbox'][0]:.0f}x{obj['bbox'][3]-obj['bbox'][1]:.0f}"
            })
        
        return metadata

# YOLO 모델 로드 (person 클래스만 사용)
model = YOLO('yolov8n-seg.pt')  # 필요시 경로 수정
#model = YOLO('yolov8s-seg.pt')
#model = YOLO('yolo11n-seg.pt')


UPLOADS_DIR = 'uploads'
RESULTS_DIR = 'results'
MAX_FILES = 30
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def save_and_limit_dir(directory, filename, image):
    """이미지 저장 및 최대 개수 제한"""
    path = os.path.join(directory, filename)
    image.save(path)
    # 파일 개수 제한
    files = sorted([os.path.join(directory, f) for f in os.listdir(directory)], key=os.path.getctime)
    if len(files) > MAX_FILES:
        for f in files[:-MAX_FILES]:
            try:
                os.remove(f)
            except Exception as e:
                print(f"[파일 삭제 오류] {f}: {e}")
    return path

def log_with_time(msg):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {msg}")

last_receive_time = None

@app.route('/detect_person', methods=['POST'])
def detect_person():
    global last_receive_time
    start_time = time.time()
    now = start_time
    # 수신 간격 계산
    if last_receive_time is not None:
        interval_ms = int((now - last_receive_time) * 1000)
        log_with_time(f"[detect_person] 이전 요청 대비 수신 간격: {interval_ms} ms")
    last_receive_time = now
    if 'image' not in request.files:
        log_with_time("[detect_person] 이미지가 업로드되지 않았습니다.")
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    log_with_time(f"[detect_person] 이미지 수신: {file.filename}")
    img = Image.open(file.stream).convert('RGB')

    # 파일명 생성 (타임스탬프+파일명)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    base_name = os.path.splitext(file.filename)[0]
    upload_filename = f"{timestamp}_{base_name}.jpg"
    result_filename = f"{timestamp}_{base_name}_result.jpg"

    # 1. 원본 이미지 저장 (최대 30개)
    save_and_limit_dir(UPLOADS_DIR, upload_filename, img)

    # 2. YOLO 추론 및 결과 이미지 생성
    results = model(img)
    person_detected = False
    person_count = 0  # 사람 감지 개수
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
                color = (0,255,0) if cls == 0 else (255,0,0)
                label = f"{model.names[cls]} {conf:.2f}"
                # 박스 그리기
                cv2.rectangle(result_img_np, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(result_img_np, label, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                if cls == 0:
                    person_detected = True
                    person_count += 1
    
    # 결과 이미지 저장 (최대 30개)
    result_img_pil = Image.fromarray(result_img_np)
    
    # 우하단에 사람 감지 개수 표시
    h, w = result_img_np.shape[:2]
    if person_detected:
        # 사람 감지 개수 텍스트 (영어)
        text = f'People: {person_count}'
        color = (0, 0, 255)  # 빨간색 (BGR) - 사람 감지 시
        
        # 텍스트 크기 계산
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 좌하단 위치 계산 (여백 20픽셀)
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
    else:
        # 사람이 감지되지 않은 경우 (영어)
        text = 'No People'
        color = (0, 255, 0)  # 초록색 (BGR) - 사람 비감지 시
        
        # 텍스트 크기 계산
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 좌하단 위치 계산 (여백 20픽셀)
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
    save_and_limit_dir(RESULTS_DIR, result_filename, result_img_pil)

    status = "stop" if person_detected else "go"
    log_with_time(f"[detect_person] 결과: {status}, 사람 수: {person_count}명")
    end_time = time.time()
    elapsed_ms = int((end_time - start_time) * 1000)
    log_with_time(f"[detect_person] 처리~송신까지 소요 시간: {elapsed_ms} ms")
    return jsonify({'status': status, 'person_count': person_count})

@app.route('/health', methods=['GET'])
def health():
    log_with_time("[health] 헬스체크 요청 수신!")
    return jsonify({'status': 'ok'})

@app.route('/stream_results')
def stream_results():
    """results 폴더의 이미지를 연속적으로 보여주는 웹페이지"""
    return render_template('results_stream.html')

@app.route('/api/latest_result_image')
def api_latest_result_image():
    """results 폴더에서 가장 최근 이미지를 base64로 반환 (UDP처럼 신뢰성 없이)"""
    try:
        files = [f for f in os.listdir(RESULTS_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            return jsonify({'success': False, 'error': 'No result images'}), 404
        files.sort(key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
        latest_file = os.path.join(RESULTS_DIR, files[0])
        with open(latest_file, 'rb') as f:
            img_bytes = f.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return jsonify({'success': True, 'image': img_base64, 'filename': files[0]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/events')
def sse_events():
    def event_stream():
        last_filename = None
        while True:
            files = [f for f in os.listdir(RESULTS_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if files:
                files.sort(key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
                latest_file = files[0]
                if latest_file != last_filename:
                    last_filename = latest_file
                    yield f'data: {latest_file}\n\n'
            time.sleep(0.5)
    return Response(event_stream(), mimetype='text/event-stream')

def main():
    """서비스 데모"""
    import argparse
    
    parser = argparse.ArgumentParser(description='세그멘테이션 서비스 데모')
    parser.add_argument('image_path', help='입력 이미지 경로')
    parser.add_argument('--service', choices=['remove_bg', 'extract', 'beauty', 'count', 'analyze', 'collage'], 
                       default='analyze', help='사용할 서비스')
    parser.add_argument('--output', help='출력 파일 경로')
    parser.add_argument('--show', action='store_true', help='결과 표시')
    
    args = parser.parse_args()
    
    # 서비스 초기화
    services = SegmentationServices()
    
    # 이미지 로드
    image = cv2.imread(args.image_path)
    if image is None:
        print(f"❌ 이미지를 로드할 수 없습니다: {args.image_path}")
        return
    
    print(f"🔧 {args.service} 서비스 실행 중...")
    
    # 서비스 실행
    if args.service == 'remove_bg':
        result, mask = services.remove_background(image)
        print("✅ 배경 제거 완료")
        
    elif args.service == 'extract':
        objects = services.extract_objects(image, ['person', 'car', 'dog', 'cat'])
        print(f"✅ {len(objects)}개 객체 추출 완료")
        result = services.create_collage(image)
        
    elif args.service == 'beauty':
        result = services.apply_face_beauty(image)
        print("✅ 얼굴 뷰티 필터 적용 완료")
        
    elif args.service == 'count':
        counts, result_image = services.count_objects(image)
        print("📊 객체 개수:")
        for obj, count in counts.items():
            print(f"  {obj}: {count}개")
        result = result_image
        
    elif args.service == 'analyze':
        analysis = services.analyze_image(image)
        print("📊 이미지 분석 결과:")
        print(f"  총 객체 수: {analysis['total_objects']}")
        print(f"  객체 종류: {', '.join(analysis['object_counts'].keys())}")
        print(f"  주요 객체: {', '.join(analysis['dominant_objects'])}")
        result = image
        
    elif args.service == 'collage':
        result = services.create_collage(image)
        print("✅ 콜라주 생성 완료")
    
    # 결과 저장
    if args.output:
        cv2.imwrite(args.output, result)
        print(f"💾 결과 저장: {args.output}")
    else:
        output_path = f"result_{args.service}.jpg"
        cv2.imwrite(output_path, result)
        print(f"💾 결과 저장: {output_path}")
    
    # 결과 표시
    if args.show:
        cv2.imshow(f'{args.service} Result', result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 
    
    