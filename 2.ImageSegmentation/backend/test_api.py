#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO API 테스트 스크립트
웹 서버가 실행 중일 때 API를 테스트할 수 있습니다.
"""

import requests
import json
import os
from pathlib import Path

def test_api_with_image(image_path, api_url="http://localhost:5000/api/detect"):
    """이미지 파일로 API 테스트"""
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return None
    
    print(f"🔄 API 테스트 중 (파일): {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API 호출 성공!")
            print(f"📊 감지된 객체 수: {result.get('total_objects', 0)}")
            
            # 감지 결과 출력
            detections = result.get('detections', [])
            for i, detection in enumerate(detections, 1):
                print(f"  {i}. {detection['class_name']} (신뢰도: {detection['confidence']:.2f})")
                print(f"     위치: {detection['bbox']}")
            
            return result
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None

def test_api_with_url(image_url, api_url="http://localhost:5000/api/detect"):
    """이미지 URL로 API 테스트"""
    
    print(f"🔄 API 테스트 중 (URL): {image_url}")
    
    try:
        data = {'image_url': image_url}
        response = requests.post(api_url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API 호출 성공!")
            print(f"📊 감지된 객체 수: {result.get('total_objects', 0)}")
            
            # 감지 결과 출력
            detections = result.get('detections', [])
            for i, detection in enumerate(detections, 1):
                print(f"  {i}. {detection['class_name']} (신뢰도: {detection['confidence']:.2f})")
                print(f"     위치: {detection['bbox']}")
            
            return result
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None

def test_web_interface(base_url="http://localhost:5000"):
    """웹 인터페이스 연결 테스트"""
    
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ 웹 인터페이스 접속 가능")
            print(f"🌐 URL: {base_url}")
            return True
        else:
            print(f"❌ 웹 인터페이스 접속 실패: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 웹 인터페이스에 연결할 수 없습니다.")
        return False

def create_test_image():
    """테스트용 간단한 이미지 생성 (OpenCV 필요)"""
    try:
        import cv2
        import numpy as np
        
        # 400x300 크기의 테스트 이미지 생성
        img = np.ones((300, 400, 3), dtype=np.uint8) * 255
        
        # 간단한 도형 그리기 (사각형)
        cv2.rectangle(img, (100, 100), (300, 200), (0, 255, 0), -1)
        
        # 원 그리기
        cv2.circle(img, (200, 150), 30, (255, 0, 0), -1)
        
        # 텍스트 추가
        cv2.putText(img, 'Test Image', (150, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        test_image_path = 'test_image.jpg'
        cv2.imwrite(test_image_path, img)
        print(f"✅ 테스트 이미지 생성: {test_image_path}")
        return test_image_path
        
    except ImportError:
        print("❌ OpenCV가 설치되지 않아 테스트 이미지를 생성할 수 없습니다.")
        return None

def main():
    print("🧪 YOLO API 테스트")
    print("=" * 50)
    
    # 웹 인터페이스 테스트
    print("1. 웹 인터페이스 연결 테스트...")
    web_ok = test_web_interface()
    
    # API 테스트
    print("\n2. API 테스트...")
    
    # 테스트 이미지 찾기
    test_images = [
        'test_image.jpg',
        'sample.jpg',
        'image.jpg',
        'test.png'
    ]
    
    test_image_path = None
    for img_path in test_images:
        if os.path.exists(img_path):
            test_image_path = img_path
            break
    
    # 테스트 이미지가 없으면 생성
    if test_image_path is None:
        print("📸 테스트 이미지가 없습니다. 생성 중...")
        test_image_path = create_test_image()
    
    # 파일 업로드 테스트
    file_result = None
    if test_image_path:
        file_result = test_api_with_image(test_image_path)
    
    # URL 테스트
    print("\n3. URL 테스트...")
    test_urls = [
        'https://ultralytics.com/images/bus.jpg',
        'https://ultralytics.com/images/zidane.jpg'
    ]
    
    url_result = None
    for url in test_urls:
        print(f"\n테스트 URL: {url}")
        url_result = test_api_with_url(url)
        if url_result:
            break
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📋 테스트 결과 요약:")
    print(f"  - 웹 인터페이스: {'✅' if web_ok else '❌'}")
    print(f"  - 파일 업로드 API: {'✅' if file_result else '❌'}")
    print(f"  - URL 업로드 API: {'✅' if url_result else '❌'}")
    
    if file_result:
        print(f"  - 파일에서 감지된 객체: {file_result.get('total_objects', 0)}개")
    if url_result:
        print(f"  - URL에서 감지된 객체: {url_result.get('total_objects', 0)}개")
    
    if web_ok and (file_result or url_result):
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패")

if __name__ == '__main__':
    main() 