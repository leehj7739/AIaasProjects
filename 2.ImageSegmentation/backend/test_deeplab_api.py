#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepLabV3+ 세그멘테이션 API 테스트 스크립트
"""

import requests
import json
import os
from pathlib import Path

def test_deeplab_api_with_image(image_path, api_url="http://localhost:5001/api/road_segmentation"):
    """이미지 파일로 DeepLabV3+ API 테스트"""
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return None
    
    print(f"🔄 DeepLabV3+ API 테스트 중 (파일): {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ DeepLabV3+ API 호출 성공!")
            print(f"📊 감지된 도로 객체 수: {result.get('total_objects', 0)}")
            
            # 장면 분석 결과 출력
            scene_analysis = result.get('scene_analysis', {})
            if scene_analysis:
                print(f"🚶 보행자 수: {scene_analysis.get('pedestrian_count', 0)}")
                print(f"🚗 차량 수: {scene_analysis.get('vehicle_count', 0)}")
                print(f"🚦 신호등 수: {scene_analysis.get('traffic_signals', 0)}")
                print(f"🛣️ 교통 밀도: {scene_analysis.get('traffic_density', 0):.2f}")
                print(f"🛡️ 안전 점수: {scene_analysis.get('road_safety_score', 0)}")
            
            # 도로 객체 상세 정보
            road_objects = result.get('road_objects', [])
            for i, obj in enumerate(road_objects, 1):
                print(f"  {i}. {obj['class_name']} (면적: {obj['area']:.0f})")
                print(f"     위치: {obj['bbox']}")
            
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

def test_deeplab_api_with_url(image_url, api_url="http://localhost:5001/api/road_segmentation"):
    """이미지 URL로 DeepLabV3+ API 테스트"""
    
    print(f"🔄 DeepLabV3+ API 테스트 중 (URL): {image_url}")
    
    try:
        data = {'image_url': image_url}
        response = requests.post(api_url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ DeepLabV3+ API 호출 성공!")
            print(f"📊 감지된 도로 객체 수: {result.get('total_objects', 0)}")
            
            # 장면 분석 결과 출력
            scene_analysis = result.get('scene_analysis', {})
            if scene_analysis:
                print(f"🚶 보행자 수: {scene_analysis.get('pedestrian_count', 0)}")
                print(f"🚗 차량 수: {scene_analysis.get('vehicle_count', 0)}")
                print(f"🚦 신호등 수: {scene_analysis.get('traffic_signals', 0)}")
                print(f"🛣️ 교통 밀도: {scene_analysis.get('traffic_density', 0):.2f}")
                print(f"🛡️ 안전 점수: {scene_analysis.get('road_safety_score', 0)}")
            
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

def test_health_check(api_url="http://localhost:5001/health"):
    """헬스 체크 테스트"""
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            result = response.json()
            print("✅ DeepLabV3+ 서버 정상 동작 중!")
            print(f"🔧 서비스: {result.get('service', 'Unknown')}")
            print(f"💻 디바이스: {result.get('device', 'Unknown')}")
            return True
        else:
            print(f"❌ 서버 상태 확인 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        return False

def test_go_stop_api(image_path, api_url="http://localhost:5001/api/go_stop"):
    """GO/STOP API 테스트"""
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return None
    
    print(f"🔄 GO/STOP API 테스트 중 (파일): {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ GO/STOP API 호출 성공!")
            print(f"🚦 상태: {result.get('status', 'unknown').upper()}")
            print(f"🚶 보행자 수: {result.get('person_count', 0)}")
            print(f"💬 메시지: {result.get('message', 'N/A')}")
            
            if result.get('visualization_filename'):
                print(f"🖼️ 결과 이미지: {result.get('visualization_filename')}")
            
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

def test_go_stop_api_with_url(image_url, api_url="http://localhost:5001/api/go_stop"):
    """URL로 GO/STOP API 테스트"""
    
    print(f"🔄 GO/STOP API 테스트 중 (URL): {image_url}")
    
    try:
        data = {'image_url': image_url}
        response = requests.post(api_url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ GO/STOP API 호출 성공!")
            print(f"🚦 상태: {result.get('status', 'unknown').upper()}")
            print(f"🚶 보행자 수: {result.get('person_count', 0)}")
            print(f"💬 메시지: {result.get('message', 'N/A')}")
            
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

if __name__ == "__main__":
    print("🧪 DeepLabV3+ 세그멘테이션 API 테스트 시작...")
    
    # 1. 헬스 체크
    print("\n1️⃣ 서버 상태 확인")
    if not test_health_check():
        print("❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작하세요.")
        exit(1)
    
    # 2. 테스트 이미지로 API 테스트
    print("\n2️⃣ 로컬 이미지로 테스트")
    test_images = [
        "uploads/test_image.jpg",
        "results/test_result.jpg"
    ]
    
    for img_path in test_images:
        if os.path.exists(img_path):
            test_deeplab_api_with_image(img_path)
            break
    else:
        print("⚠️ 테스트용 이미지가 없습니다. URL 테스트를 진행합니다.")
    
    # 3. URL로 API 테스트
    print("\n3️⃣ URL로 테스트")
    test_urls = [
        "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=640&h=480",
        "https://images.unsplash.com/photo-1549924231-f129b911e442?w=640&h=480"
    ]
    
    for url in test_urls:
        test_deeplab_api_with_url(url)
        break
    
    # 4. GO/STOP API 테스트
    print("\n4️⃣ GO/STOP API 테스트")
    for img_path in test_images:
        if os.path.exists(img_path):
            test_go_stop_api(img_path)
            break
    else:
        print("⚠️ 테스트용 이미지가 없습니다. URL로 GO/STOP 테스트를 진행합니다.")
        for url in test_urls:
            test_go_stop_api_with_url(url)
            break
    
    print("\n✅ 테스트 완료!") 