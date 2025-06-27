#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 YOLO 이미지 세그멘테이션 데모
웹 서버 없이 콘솔에서 실행할 수 있는 버전
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os
import argparse
from pathlib import Path
import torch

# PyTorch 2.6 호환성을 위한 설정
torch.serialization.add_safe_globals(['ultralytics.nn.tasks.SegmentationModel'])

def load_model(model_path='yolov8n-seg.pt'):
    """YOLO 모델 로드"""
    print(f"🔄 모델 로딩 중: {model_path}")
    model = YOLO(model_path)
    print("✅ 모델 로드 완료!")
    return model

def process_image(model, image_path, output_path=None, conf_threshold=0.25):
    """이미지에서 객체 감지 및 세그멘테이션"""
    
    # 이미지 로드
    print(f"📸 이미지 로딩: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 이미지를 로드할 수 없습니다: {image_path}")
        return None
    
    print(f"📏 이미지 크기: {image.shape[1]}x{image.shape[0]}")
    
    # YOLO 추론
    print("🔍 객체 감지 중...")
    results = model(image, conf=conf_threshold)
    
    # 결과 처리
    detections = []
    segmented_image = image.copy()
    
    for result in results:
        boxes = result.boxes
        masks = result.masks
        
        if boxes is not None:
            print(f"🎯 {len(boxes)}개의 객체 감지됨")
            
            for i, box in enumerate(boxes):
                # 바운딩 박스 정보
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                
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
                
                detections.append(detection)
                
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
        
        else:
            print("❌ 감지된 객체가 없습니다.")
    
    # 결과 출력
    print("\n📊 감지 결과:")
    for i, detection in enumerate(detections, 1):
        print(f"  {i}. {detection['class_name']} (신뢰도: {detection['confidence']:.2f})")
        print(f"     위치: [{detection['bbox'][0]:.0f}, {detection['bbox'][1]:.0f}, {detection['bbox'][2]:.0f}, {detection['bbox'][3]:.0f}]")
        print(f"     면적: {detection['area']:.0f} 픽셀")
    
    # 결과 이미지 저장
    if output_path is None:
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_segmented{input_path.suffix}"
    
    cv2.imwrite(str(output_path), segmented_image)
    print(f"\n💾 결과 이미지 저장: {output_path}")
    
    return detections, segmented_image

def main():
    parser = argparse.ArgumentParser(description='YOLO 이미지 세그멘테이션 데모')
    parser.add_argument('image_path', help='처리할 이미지 경로')
    parser.add_argument('--model', default='yolov8n-seg.pt', help='YOLO 모델 경로 (기본값: yolov8n-seg.pt)')
    parser.add_argument('--output', help='출력 이미지 경로')
    parser.add_argument('--conf', type=float, default=0.25, help='신뢰도 임계값 (기본값: 0.25)')
    parser.add_argument('--show', action='store_true', help='결과 이미지 표시')
    
    args = parser.parse_args()
    
    # 모델 로드
    model = load_model(args.model)
    
    # 이미지 처리
    result = process_image(model, args.image_path, args.output, args.conf)
    
    if result is not None:
        detections, segmented_image = result
        
        # 결과 이미지 표시
        if args.show:
            print("\n🖼️ 결과 이미지를 표시합니다. 아무 키나 누르면 종료됩니다.")
            cv2.imshow('YOLO Segmentation Result', segmented_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

if __name__ == '__main__':
    print("🎯 YOLO 이미지 세그멘테이션 데모")
    print("=" * 50)
    
    # 명령행 인수가 없으면 대화형 모드
    import sys
    if len(sys.argv) == 1:
        print("대화형 모드로 실행합니다.")
        print("사용법: python simple_demo.py <이미지경로> [옵션]")
        print("\n예시:")
        print("  python simple_demo.py image.jpg")
        print("  python simple_demo.py image.jpg --conf 0.5 --show")
        print("  python simple_demo.py image.jpg --output result.jpg")
        print("\n옵션:")
        print("  --model: 모델 파일 경로 (기본값: yolov8n-seg.pt)")
        print("  --output: 출력 파일 경로")
        print("  --conf: 신뢰도 임계값 (0.0-1.0)")
        print("  --show: 결과 이미지 표시")
    else:
        main() 