#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 세그멘테이션 서비스 데모
다양한 세그멘테이션 후처리 서비스를 콘솔에서 테스트할 수 있습니다.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import argparse
import os
from pathlib import Path
import json

# PyTorch 2.6 호환성 설정
import torch
torch.serialization.add_safe_globals(['ultralytics.nn.tasks.SegmentationModel'])

class SegmentationServicesDemo:
    def __init__(self):
        """서비스 데모 초기화"""
        print("🔧 세그멘테이션 서비스 초기화 중...")
        
        # YOLO 모델 로드
        self.yolo_model = YOLO('yolov8n-seg.pt')
        
        # MediaPipe 얼굴 랜드마크
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # 결과 폴더 생성
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)
        
        print("✅ 서비스 초기화 완료!")

    def load_image(self, image_path):
        """이미지 로드"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
        
        return image

    def save_result(self, image, filename):
        """결과 이미지 저장"""
        result_path = self.results_dir / filename
        cv2.imwrite(str(result_path), image)
        print(f"💾 결과 저장: {result_path}")
        return str(result_path)

    def demo_background_removal(self, image_path, target_class='person'):
        """배경 제거 데모"""
        print(f"\n🎯 배경 제거 서비스 데모")
        print(f"📁 이미지: {image_path}")
        print(f"🎯 대상 객체: {target_class}")
        
        image = self.load_image(image_path)
        
        # 객체 감지
        results = self.yolo_model(image)
        
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
        
        # 결과 저장
        filename = f"bg_removed_{target_class}.png"
        self.save_result(result_image, filename)
        
        print("✅ 배경 제거 완료!")
        return result_image

    def demo_object_extraction(self, image_path, target_classes=None):
        """객체 추출 데모"""
        print(f"\n✂️ 객체 추출 서비스 데모")
        print(f"📁 이미지: {image_path}")
        print(f"🎯 대상 객체: {target_classes or '모든 객체'}")
        
        image = self.load_image(image_path)
        results = self.yolo_model(image)
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
                        
                        # 결과 저장
                        filename = f"extracted_{class_name}_{len(extracted_objects)}.png"
                        self.save_result(extracted, filename)
                        
                        extracted_objects.append({
                            'class': class_name,
                            'filename': filename,
                            'confidence': float(box.conf[0].cpu().numpy())
                        })
        
        print(f"✅ {len(extracted_objects)}개 객체 추출 완료!")
        for obj in extracted_objects:
            print(f"  - {obj['class']} (신뢰도: {obj['confidence']:.2f})")
        
        return extracted_objects

    def demo_face_beauty(self, image_path):
        """얼굴 뷰티 데모"""
        print(f"\n💄 얼굴 뷰티 서비스 데모")
        print(f"📁 이미지: {image_path}")
        
        image = self.load_image(image_path)
        
        # 얼굴 랜드마크 검출
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
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
            filename = "face_beauty.jpg"
            self.save_result(result_image, filename)
            print("✅ 얼굴 뷰티 필터 적용 완료!")
        else:
            print("⚠️ 얼굴을 감지할 수 없습니다.")
        
        return result_image

    def demo_object_counting(self, image_path, target_classes=None):
        """객체 카운팅 데모"""
        print(f"\n🔢 객체 카운팅 서비스 데모")
        print(f"📁 이미지: {image_path}")
        print(f"🎯 대상 객체: {target_classes or '모든 객체'}")
        
        image = self.load_image(image_path)
        results = self.yolo_model(image)
        object_counts = {}
        object_details = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0].cpu().numpy())
                    class_name = self.yolo_model.names[cls]
                    confidence = float(box.conf[0].cpu().numpy())
                    bbox = box.xyxy[0].cpu().numpy().tolist()
                    
                    if target_classes is None or class_name in target_classes:
                        object_counts[class_name] = object_counts.get(class_name, 0) + 1
                        object_details.append({
                            'class': class_name,
                            'confidence': confidence,
                            'bbox': bbox
                        })
        
        print(f"✅ 객체 카운팅 완료!")
        print(f"📊 총 객체 수: {sum(object_counts.values())}개")
        for obj, count in object_counts.items():
            print(f"  - {obj}: {count}개")
        
        return object_counts, object_details

    def demo_image_analysis(self, image_path):
        """이미지 분석 데모"""
        print(f"\n📊 이미지 분석 서비스 데모")
        print(f"📁 이미지: {image_path}")
        
        image = self.load_image(image_path)
        results = self.yolo_model(image)
        
        analysis = {
            'objects': [],
            'total_objects': 0,
            'image_size': image.shape,
            'dominant_objects': [],
            'object_counts': {}
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
                        obj_info['mask_area'] = int(mask_area)
                    
                    analysis['objects'].append(obj_info)
                    object_counts[class_name] = object_counts.get(class_name, 0) + 1
        
        analysis['total_objects'] = len(analysis['objects'])
        analysis['object_counts'] = object_counts
        
        # 주요 객체 찾기 (면적 기준)
        if analysis['objects']:
            sorted_objects = sorted(analysis['objects'], key=lambda x: x.get('mask_area', 0), reverse=True)
            analysis['dominant_objects'] = [obj['class'] for obj in sorted_objects[:3]]
        
        print("✅ 이미지 분석 완료!")
        print(f"📐 이미지 크기: {analysis['image_size'][1]}x{analysis['image_size'][0]}")
        print(f"🎯 총 객체 수: {analysis['total_objects']}개")
        print(f"🏆 주요 객체: {', '.join(analysis['dominant_objects'])}")
        print(f"📊 객체 분포:")
        for obj, count in analysis['object_counts'].items():
            print(f"  - {obj}: {count}개")
        
        # 분석 결과 저장
        analysis_file = self.results_dir / "image_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"💾 분석 결과 저장: {analysis_file}")
        
        return analysis

    def demo_image_filter(self, image_path, filter_type='blur', target_class='person'):
        """이미지 필터 데모"""
        print(f"\n🎨 이미지 필터 서비스 데모")
        print(f"📁 이미지: {image_path}")
        print(f"🎨 필터: {filter_type}")
        print(f"🎯 대상 객체: {target_class}")
        
        image = self.load_image(image_path)
        results = self.yolo_model(image)
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
                        elif filter_type == 'contrast':
                            lab = cv2.cvtColor(result_image, cv2.COLOR_BGR2LAB)
                            lab[mask_bool, 0] = np.clip(lab[mask_bool, 0] * 1.3, 0, 255)
                            result_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 결과 저장
        filename = f"filtered_{filter_type}_{target_class}.jpg"
        self.save_result(result_image, filename)
        
        print("✅ 이미지 필터 적용 완료!")
        return result_image

    def run_all_demos(self, image_path):
        """모든 서비스 데모 실행"""
        print("🚀 모든 세그멘테이션 서비스 데모 시작!")
        print("=" * 50)
        
        try:
            # 1. 배경 제거
            self.demo_background_removal(image_path)
            
            # 2. 객체 추출
            self.demo_object_extraction(image_path, ['person', 'car', 'dog', 'cat'])
            
            # 3. 얼굴 뷰티
            self.demo_face_beauty(image_path)
            
            # 4. 객체 카운팅
            self.demo_object_counting(image_path)
            
            # 5. 이미지 분석
            self.demo_image_analysis(image_path)
            
            # 6. 이미지 필터
            self.demo_image_filter(image_path, 'blur', 'person')
            
            print("\n🎉 모든 서비스 데모 완료!")
            print(f"📁 결과 파일들은 'results' 폴더에 저장되었습니다.")
            
        except Exception as e:
            print(f"❌ 데모 실행 중 오류 발생: {e}")

def main():
    parser = argparse.ArgumentParser(description='이미지 세그멘테이션 서비스 데모')
    parser.add_argument('image_path', help='입력 이미지 경로')
    parser.add_argument('--service', choices=['all', 'bg_remove', 'extract', 'beauty', 'count', 'analyze', 'filter'], 
                       default='all', help='실행할 서비스')
    parser.add_argument('--target_class', default='person', help='대상 객체 클래스')
    parser.add_argument('--filter_type', choices=['blur', 'brightness', 'contrast'], 
                       default='blur', help='필터 종류')
    
    args = parser.parse_args()
    
    # 데모 초기화
    demo = SegmentationServicesDemo()
    
    # 서비스 실행
    if args.service == 'all':
        demo.run_all_demos(args.image_path)
    elif args.service == 'bg_remove':
        demo.demo_background_removal(args.image_path, args.target_class)
    elif args.service == 'extract':
        demo.demo_object_extraction(args.image_path, [args.target_class])
    elif args.service == 'beauty':
        demo.demo_face_beauty(args.image_path)
    elif args.service == 'count':
        demo.demo_object_counting(args.image_path)
    elif args.service == 'analyze':
        demo.demo_image_analysis(args.image_path)
    elif args.service == 'filter':
        demo.demo_image_filter(args.image_path, args.filter_type, args.target_class)

if __name__ == '__main__':
    main() 