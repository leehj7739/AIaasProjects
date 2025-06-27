#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
얼굴 세부 부위 검출 데모
눈, 코, 입, 귀 등의 얼굴 랜드마크를 검출합니다.
"""

import cv2
import numpy as np
import mediapipe as mp
import argparse
from pathlib import Path
import requests
from urllib.parse import urlparse

class FaceLandmarkDetector:
    def __init__(self):
        """얼굴 랜드마크 검출기 초기화"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # 얼굴 메시 모델 초기화 (468개 랜드마크)
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # 주요 얼굴 부위의 랜드마크 인덱스
        self.landmark_indices = {
            'left_eye': [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
            'right_eye': [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
            'nose': [1, 2, 141, 17, 18, 200, 199, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            'mouth': [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318, 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 307, 375, 321, 308, 324, 318, 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308],
            'left_ear': [234, 227, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93],
            'right_ear': [454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361, 323, 454, 356, 389, 251, 284, 332, 297, 338, 10, 109, 67, 103, 54, 21, 162, 127, 234, 93]
        }
        
        # 색상 정의
        self.colors = {
            'left_eye': (0, 255, 0),    # 녹색
            'right_eye': (0, 255, 0),   # 녹색
            'nose': (255, 0, 0),        # 파란색
            'mouth': (0, 0, 255),       # 빨간색
            'left_ear': (255, 255, 0),  # 청록색
            'right_ear': (255, 255, 0)  # 청록색
        }

    def download_image_from_url(self, url):
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

    def detect_landmarks(self, image):
        """얼굴 랜드마크 검출"""
        # BGR을 RGB로 변환
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 얼굴 랜드마크 검출
        results = self.face_mesh.process(rgb_image)
        
        landmarks_data = {}
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # 이미지 크기 가져오기
                h, w, _ = image.shape
                
                # 각 얼굴 부위별로 랜드마크 추출
                for part_name, indices in self.landmark_indices.items():
                    landmarks = []
                    for idx in indices:
                        if idx < len(face_landmarks.landmark):
                            landmark = face_landmarks.landmark[idx]
                            x = int(landmark.x * w)
                            y = int(landmark.y * h)
                            landmarks.append((x, y))
                    
                    landmarks_data[part_name] = landmarks
        
        return landmarks_data

    def draw_landmarks(self, image, landmarks_data):
        """랜드마크를 이미지에 그리기"""
        result_image = image.copy()
        
        for part_name, landmarks in landmarks_data.items():
            if landmarks:
                color = self.colors[part_name]
                
                # 랜드마크 점 그리기
                for point in landmarks:
                    cv2.circle(result_image, point, 2, color, -1)
                
                # 부위별 윤곽선 그리기
                if len(landmarks) > 2:
                    # 볼록 껍질(Convex Hull) 계산
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

    def analyze_face_parts(self, landmarks_data):
        """얼굴 부위 분석"""
        analysis = {}
        
        for part_name, landmarks in landmarks_data.items():
            if landmarks:
                # 면적 계산 (랜드마크로 둘러싸인 영역)
                if len(landmarks) > 2:
                    landmarks_array = np.array(landmarks, dtype=np.int32)
                    area = cv2.contourArea(landmarks_array)
                    analysis[part_name] = {
                        'landmark_count': len(landmarks),
                        'area': area,
                        'center': (sum(p[0] for p in landmarks) // len(landmarks),
                                 sum(p[1] for p in landmarks) // len(landmarks))
                    }
        
        return analysis

def main():
    parser = argparse.ArgumentParser(description='얼굴 세부 부위 검출 데모')
    parser.add_argument('input', help='이미지 파일 경로 또는 URL')
    parser.add_argument('--output', help='출력 이미지 경로')
    parser.add_argument('--show', action='store_true', help='결과 이미지 표시')
    
    args = parser.parse_args()
    
    # 검출기 초기화
    detector = FaceLandmarkDetector()
    
    # 이미지 로드
    print(f"📸 이미지 로딩: {args.input}")
    
    if args.input.startswith(('http://', 'https://')):
        image = detector.download_image_from_url(args.input)
    else:
        image = cv2.imread(args.input)
        if image is None:
            print(f"❌ 이미지를 로드할 수 없습니다: {args.input}")
            return
    
    print(f"📏 이미지 크기: {image.shape[1]}x{image.shape[0]}")
    
    # 얼굴 랜드마크 검출
    print("🔍 얼굴 랜드마크 검출 중...")
    landmarks_data = detector.detect_landmarks(image)
    
    if not landmarks_data:
        print("❌ 얼굴을 찾을 수 없습니다.")
        return
    
    # 결과 분석
    analysis = detector.analyze_face_parts(landmarks_data)
    
    print("\n📊 검출된 얼굴 부위:")
    for part_name, data in analysis.items():
        print(f"  {part_name.replace('_', ' ').title()}:")
        print(f"    - 랜드마크 수: {data['landmark_count']}")
        print(f"    - 면적: {data['area']:.0f} 픽셀")
        print(f"    - 중심점: {data['center']}")
    
    # 결과 이미지 생성
    result_image = detector.draw_landmarks(image, landmarks_data)
    
    # 결과 저장
    if args.output is None:
        input_path = Path(args.input)
        if args.input.startswith(('http://', 'https://')):
            output_path = f"face_landmarks_result.jpg"
        else:
            output_path = input_path.parent / f"{input_path.stem}_face_landmarks{input_path.suffix}"
    else:
        output_path = args.output
    
    cv2.imwrite(str(output_path), result_image)
    print(f"\n💾 결과 이미지 저장: {output_path}")
    
    # 결과 표시
    if args.show:
        print("\n🖼️ 결과 이미지를 표시합니다. 아무 키나 누르면 종료됩니다.")
        cv2.imshow('Face Landmarks Detection', result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    print("👤 얼굴 세부 부위 검출 데모")
    print("=" * 50)
    
    import sys
    if len(sys.argv) == 1:
        print("사용법: python face_detection_demo.py <이미지경로 또는 URL> [옵션]")
        print("\n예시:")
        print("  python face_detection_demo.py face.jpg")
        print("  python face_detection_demo.py https://example.com/face.jpg --show")
        print("  python face_detection_demo.py face.jpg --output result.jpg")
        print("\n옵션:")
        print("  --output: 출력 파일 경로")
        print("  --show: 결과 이미지 표시")
    else:
        main() 