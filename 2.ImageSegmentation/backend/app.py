from flask import Flask, request, jsonify, render_template, send_file
from ultralytics import YOLO
import cv2
import numpy as np
import os
import base64
from PIL import Image
import io
import json
import torch
import requests
from urllib.parse import urlparse
import mediapipe as mp

# PyTorch 2.6 호환성을 위한 설정
torch.serialization.add_safe_globals(['ultralytics.nn.tasks.SegmentationModel'])

app = Flask(__name__)

# YOLO 모델 로드 (가장 가벼운 세그멘테이션 모델)
model = YOLO('yolov8n-seg.pt')

# MediaPipe 얼굴 랜드마크 검출기 초기화
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# 주요 얼굴 부위의 랜드마크 인덱스
FACE_LANDMARK_INDICES = {
    'left_eye': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
    'right_eye': [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
    'nose': [1, 2, 141, 17, 18, 200, 199, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    'mouth': [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318, 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 307, 375, 321, 308, 324, 318, 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308],
    'left_ear': [234, 227, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93],
    'right_ear': [454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93]
}

# 얼굴 부위별 색상
FACE_COLORS = {
    'left_eye': (0, 255, 0),    # 녹색
    'right_eye': (0, 255, 0),   # 녹색
    'nose': (255, 0, 0),        # 파란색
    'mouth': (0, 0, 255),       # 빨간색
    'left_ear': (255, 255, 0),  # 청록색
    'right_ear': (255, 255, 0)  # 청록색
}

# 업로드 폴더 생성
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def download_image_from_url(url):
    """URL에서 이미지 다운로드"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 이미지 데이터를 numpy 배열로 변환
        image_array = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("이미지를 디코딩할 수 없습니다")
        
        return image
    except Exception as e:
        raise Exception(f"이미지 다운로드 실패: {str(e)}")

def detect_face_landmarks(image):
    """얼굴 랜드마크 검출"""
    # BGR을 RGB로 변환
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 얼굴 랜드마크 검출
    results = face_mesh.process(rgb_image)
    
    landmarks_data = {}
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # 이미지 크기 가져오기
            h, w, _ = image.shape
            
            # 각 얼굴 부위별로 랜드마크 추출
            for part_name, indices in FACE_LANDMARK_INDICES.items():
                landmarks = []
                for idx in indices:
                    if idx < len(face_landmarks.landmark):
                        landmark = face_landmarks.landmark[idx]
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        landmarks.append([x, y])
                
                landmarks_data[part_name] = landmarks
    
    return landmarks_data

def process_image_with_yolo(image):
    """YOLO 모델로 이미지 처리"""
    results = model(image)
    
    # 결과 처리
    detections = []
    segmented_image = image.copy()
    person_count = 0  # 사람 감지 개수
    
    for result in results:
        boxes = result.boxes
        masks = result.masks
        
        if boxes is not None:
            for i, box in enumerate(boxes):
                # 바운딩 박스 정보
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                
                # 사람 클래스인지 확인 (COCO 데이터셋에서 person은 클래스 0)
                if model.names[cls] == 'person':
                    person_count += 1
                
                # 세그멘테이션 마스크
                mask = None
                if masks is not None and i < len(masks.data):
                    mask = masks.data[i].cpu().numpy()
                
                detection = {
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf),
                    'class': cls,
                    'class_name': model.names[cls],
                    'area': float((x2 - x1) * (y2 - y1))
                }
                
                # 마스크가 있으면 세그멘테이션 이미지에 그리기
                if mask is not None:
                    # 마스크를 이미지 크기에 맞게 조정
                    mask_resized = cv2.resize(mask, (image.shape[1], image.shape[0]))
                    mask_bool = mask_resized > 0.5
                    
                    # 랜덤 색상 생성
                    color = np.random.randint(0, 255, 3).tolist()
                    
                    # 마스크 영역에 색상 적용
                    segmented_image[mask_bool] = segmented_image[mask_bool] * 0.5 + np.array(color) * 0.5
                    
                    # 바운딩 박스 그리기
                    cv2.rectangle(segmented_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    
                    # 라벨 그리기
                    label = f"{model.names[cls]} {conf:.2f}"
                    cv2.putText(segmented_image, label, (int(x1), int(y1)-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                detections.append(detection)
    
    # 사람 감지 개수를 좌하단에 표시
    if person_count > 0:
        # 텍스트 배경을 위한 사각형 그리기
        text = f"People: {person_count}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        
        # 텍스트 크기 계산
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 이미지 크기
        img_height, img_width = image.shape[:2]
        
        # 좌하단 위치 계산 (여백 20픽셀)
        text_x = 20
        text_y = img_height - 20
        
        # 배경 사각형 그리기
        cv2.rectangle(segmented_image, 
                     (text_x - 10, text_y - text_height - 10),
                     (text_x + text_width + 10, text_y + 10),
                     (0, 0, 0), -1)
        
        # 텍스트 그리기 (빨간색 - 사람 감지 시)
        cv2.putText(segmented_image, text, (text_x, text_y), 
                   font, font_scale, (0, 0, 255), thickness)
    else:
        # 사람이 감지되지 않은 경우
        text = "No People"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        
        # 텍스트 크기 계산
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # 이미지 크기
        img_height, img_width = image.shape[:2]
        
        # 좌하단 위치 계산 (여백 20픽셀)
        text_x = 20
        text_y = img_height - 20
        
        # 배경 사각형 그리기
        cv2.rectangle(segmented_image, 
                     (text_x - 10, text_y - text_height - 10),
                     (text_x + text_width + 10, text_y + 10),
                     (0, 0, 0), -1)
        
        # 텍스트 그리기 (초록색 - 사람 비감지 시)
        cv2.putText(segmented_image, text, (text_x, text_y), 
                   font, font_scale, (0, 255, 0), thickness)
    
    return detections, segmented_image

def draw_face_landmarks(image, landmarks_data):
    """얼굴 랜드마크를 이미지에 그리기"""
    result_image = image.copy()
    
    for part_name, landmarks in landmarks_data.items():
        if landmarks:
            color = FACE_COLORS[part_name]
            
            # 랜드마크 점 그리기
            for point in landmarks:
                cv2.circle(result_image, (point[0], point[1]), 2, color, -1)
            
            # 부위별 윤곽선 그리기
            if len(landmarks) > 2:
                landmarks_array = np.array(landmarks, dtype=np.int32)
                hull = cv2.convexHull(landmarks_array)
                cv2.polylines(result_image, [hull], True, color, 2)
            
            # 부위 이름 표시
            if landmarks:
                center_x = sum(p[0] for p in landmarks) // len(landmarks)
                center_y = sum(p[1] for p in landmarks) // len(landmarks)
                cv2.putText(result_image, part_name.replace('_', ' ').title(), 
                          (center_x, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                          0.5, color, 1)
    
    return result_image

@app.route('/')
def index():
    """메인 페이지 - 이미지 업로드 폼"""
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect_objects():
    """이미지에서 객체 감지 및 세그멘테이션"""
    try:
        image = None
        
        # 파일 업로드 확인
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                # 파일에서 이미지 읽기
                image_bytes = file.read()
                image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # URL 업로드 확인
        elif 'image_url' in request.form and request.form['image_url'].strip():
            url = request.form['image_url'].strip()
            if not url:
                return jsonify({'error': '이미지 URL이 비어있습니다'}), 400
            
            # URL 유효성 검사
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({'error': '유효하지 않은 URL입니다'}), 400
            
            # URL에서 이미지 다운로드
            image = download_image_from_url(url)
        
        else:
            return jsonify({'error': '이미지 파일 또는 URL이 필요합니다'}), 400
        
        if image is None:
            return jsonify({'error': '이미지를 읽을 수 없습니다'}), 400
        
        # 처리 모드 확인
        mode = request.form.get('mode', 'yolo')  # 기본값은 YOLO
        
        if mode == 'face_landmarks':
            # 얼굴 랜드마크 검출
            landmarks_data = detect_face_landmarks(image)
            
            if not landmarks_data:
                return jsonify({'error': '얼굴을 찾을 수 없습니다'}), 400
            
            # 얼굴 랜드마크 그리기
            result_image = draw_face_landmarks(image, landmarks_data)
            
            # 결과 데이터 구성
            detections = []
            for part_name, landmarks in landmarks_data.items():
                if landmarks:
                    # 바운딩 박스 계산
                    x_coords = [p[0] for p in landmarks]
                    y_coords = [p[1] for p in landmarks]
                    x1, x2 = min(x_coords), max(x_coords)
                    y1, y2 = min(y_coords), max(y_coords)
                    
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': 1.0,
                        'class': -1,
                        'class_name': part_name.replace('_', ' ').title(),
                        'area': float((x2 - x1) * (y2 - y1)),
                        'landmarks': landmarks
                    })
        else:
            # YOLO 모델로 세그멘테이션 수행
            detections, result_image = process_image_with_yolo(image)
            
            # 사람 감지 개수 계산
            person_count = sum(1 for det in detections if det['class_name'] == 'person')
        
        # 결과 이미지 저장
        result_filename = f"result_{len(os.listdir(RESULT_FOLDER))}.jpg"
        result_path = os.path.join(RESULT_FOLDER, result_filename)
        cv2.imwrite(result_path, result_image)
        
        # 결과 이미지를 base64로 인코딩
        _, buffer = cv2.imencode('.jpg', result_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        response_data = {
            'success': True,
            'detections': detections,
            'total_objects': len(detections),
            'result_image': img_base64,
            'result_filename': result_filename,
            'mode': mode
        }
        
        # YOLO 모드일 때만 사람 감지 개수 추가
        if mode == 'yolo':
            response_data['person_count'] = person_count
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/result/<filename>')
def get_result_image(filename):
    """결과 이미지 다운로드"""
    try:
        return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """API 엔드포인트 - JSON 응답만 반환"""
    try:
        image = None
        
        # 파일 업로드 확인
        if 'image' in request.files:
            file = request.files['image']
            image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        
        # URL 업로드 확인
        elif 'image_url' in request.form and request.form['image_url'].strip():
            url = request.form['image_url'].strip()
            if not url:
                return jsonify({'error': '이미지 URL이 비어있습니다'}), 400
            
            # URL 유효성 검사
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({'error': '유효하지 않은 URL입니다'}), 400
            
            # URL에서 이미지 다운로드
            image = download_image_from_url(url)
        
        else:
            return jsonify({'error': '이미지 파일 또는 URL이 필요합니다'}), 400
        
        if image is None:
            return jsonify({'error': '이미지를 읽을 수 없습니다'}), 400
        
        # 처리 모드 확인
        mode = request.form.get('mode', 'yolo')
        
        if mode == 'face_landmarks':
            # 얼굴 랜드마크 검출
            landmarks_data = detect_face_landmarks(image)
            
            if not landmarks_data:
                return jsonify({'error': '얼굴을 찾을 수 없습니다'}), 400
            
            # 결과 데이터 구성
            detections = []
            for part_name, landmarks in landmarks_data.items():
                if landmarks:
                    x_coords = [p[0] for p in landmarks]
                    y_coords = [p[1] for p in landmarks]
                    x1, x2 = min(x_coords), max(x_coords)
                    y1, y2 = min(y_coords), max(y_coords)
                    
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': 1.0,
                        'class': -1,
                        'class_name': part_name.replace('_', ' ').title(),
                        'landmarks': landmarks
                    })
        else:
            # YOLO 모델로 처리
            detections, _ = process_image_with_yolo(image)
            
            # 사람 감지 개수 계산
            person_count = sum(1 for det in detections if det['class_name'] == 'person')
        
        response_data = {
            'success': True,
            'detections': detections,
            'total_objects': len(detections),
            'mode': mode
        }
        
        # YOLO 모드일 때만 사람 감지 개수 추가
        if mode == 'yolo':
            response_data['person_count'] = person_count
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 YOLO 이미지 세그멘테이션 & 얼굴 랜드마크 서버 시작...")
    print("📱 웹 인터페이스: http://localhost:5000")
    print("🔗 API 엔드포인트: http://localhost:5000/api/detect")
    app.run(debug=True, host='0.0.0.0', port=5000) 