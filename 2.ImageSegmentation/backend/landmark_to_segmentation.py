#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
랜드마크를 세그멘테이션 마스크로 변환하는 예제
얼굴 랜드마크 점들을 연결하여 세그멘테이션 마스크를 생성합니다.
"""

import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path

def landmarks_to_segmentation_mask(landmarks, image_shape, fill=True):
    """
    랜드마크 점들을 세그멘테이션 마스크로 변환
    
    Args:
        landmarks: 랜드마크 좌표 리스트 [(x1, y1), (x2, y2), ...]
        image_shape: 이미지 크기 (height, width)
        fill: 내부를 채울지 여부
    
    Returns:
        mask: 세그멘테이션 마스크 (0~1 사이의 값)
    """
    if len(landmarks) < 3:
        return None
    
    # 마스크 생성
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    # 랜드마크를 numpy 배열로 변환
    landmarks_array = np.array(landmarks, dtype=np.int32)
    
    if fill:
        # 내부를 채운 다각형 그리기
        cv2.fillPoly(mask, [landmarks_array], 255)
    else:
        # 윤곽선만 그리기
        cv2.polylines(mask, [landmarks_array], True, 255, 2)
    
    # 0~1 사이의 값으로 정규화
    mask = mask.astype(np.float32) / 255.0
    
    return mask

def create_face_segmentation_from_landmarks(image_path, output_path=None):
    """
    얼굴 랜드마크를 사용하여 얼굴 세그멘테이션 마스크 생성
    """
    # MediaPipe 얼굴 메시 초기화
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )
    
    # 얼굴 윤곽 랜드마크 인덱스 (얼굴 전체 윤곽)
    face_oval_indices = [
        10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
        397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10
    ]
    
    # 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 이미지를 로드할 수 없습니다: {image_path}")
        return None
    
    # BGR을 RGB로 변환
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 얼굴 랜드마크 검출
    results = face_mesh.process(rgb_image)
    
    if not results.multi_face_landmarks:
        print("❌ 얼굴을 찾을 수 없습니다.")
        return None
    
    # 결과 이미지들
    result_images = {}
    
    for face_landmarks in results.multi_face_landmarks:
        h, w, _ = image.shape
        
        # 얼굴 윤곽 랜드마크 추출
        face_oval_landmarks = []
        for idx in face_oval_indices:
            if idx < len(face_landmarks.landmark):
                landmark = face_landmarks.landmark[idx]
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                face_oval_landmarks.append([x, y])
        
        if len(face_oval_landmarks) < 3:
            continue
        
        # 1. 원본 이미지
        result_images['original'] = image.copy()
        
        # 2. 랜드마크 점만 표시
        landmarks_image = image.copy()
        for point in face_oval_landmarks:
            cv2.circle(landmarks_image, (point[0], point[1]), 3, (0, 255, 0), -1)
        result_images['landmarks'] = landmarks_image
        
        # 3. 윤곽선만 그리기
        contour_image = image.copy()
        landmarks_array = np.array(face_oval_landmarks, dtype=np.int32)
        cv2.polylines(contour_image, [landmarks_array], True, (0, 255, 0), 2)
        result_images['contour'] = contour_image
        
        # 4. 세그멘테이션 마스크 (내부 채움)
        mask_filled = landmarks_to_segmentation_mask(face_oval_landmarks, image.shape, fill=True)
        if mask_filled is not None:
            # 마스크를 이미지에 적용
            segmentation_image = image.copy()
            mask_3d = np.stack([mask_filled] * 3, axis=2)
            segmentation_image = segmentation_image * mask_3d
            result_images['segmentation_filled'] = segmentation_image.astype(np.uint8)
            
            # 마스크만 저장
            mask_image = (mask_filled * 255).astype(np.uint8)
            result_images['mask_only'] = cv2.cvtColor(mask_image, cv2.COLOR_GRAY2BGR)
        
        # 5. 세그멘테이션 마스크 (윤곽선만)
        mask_contour = landmarks_to_segmentation_mask(face_oval_landmarks, image.shape, fill=False)
        if mask_contour is not None:
            contour_mask_image = (mask_contour * 255).astype(np.uint8)
            result_images['mask_contour'] = cv2.cvtColor(contour_mask_image, cv2.COLOR_GRAY2BGR)
    
    return result_images

def save_results(result_images, base_path):
    """결과 이미지들을 저장"""
    if not result_images:
        return
    
    base_path = Path(base_path)
    
    for name, image in result_images.items():
        output_path = base_path.parent / f"{base_path.stem}_{name}{base_path.suffix}"
        cv2.imwrite(str(output_path), image)
        print(f"💾 {name}: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='랜드마크를 세그멘테이션으로 변환')
    parser.add_argument('image_path', help='입력 이미지 경로')
    parser.add_argument('--output', help='출력 디렉토리')
    parser.add_argument('--show', action='store_true', help='결과 표시')
    
    args = parser.parse_args()
    
    print("🔄 랜드마크를 세그멘테이션으로 변환 중...")
    
    # 세그멘테이션 생성
    result_images = create_face_segmentation_from_landmarks(args.image_path)
    
    if result_images:
        # 결과 저장
        save_results(result_images, args.image_path)
        
        # 결과 표시
        if args.show:
            print("\n🖼️ 결과 이미지들을 표시합니다. 아무 키나 누르면 다음 이미지로...")
            
            for name, image in result_images.items():
                print(f"\n📸 {name}")
                cv2.imshow(name, image)
                cv2.waitKey(0)
            
            cv2.destroyAllWindows()
        
        print("\n✅ 변환 완료!")
        print("\n📋 생성된 결과:")
        for name in result_images.keys():
            print(f"  - {name}")
    else:
        print("❌ 변환 실패")

if __name__ == '__main__':
    main() 