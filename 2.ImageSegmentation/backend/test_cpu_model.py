#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU에서 DeepLabV3+ 모델 테스트
"""

import torch
import torchvision
import numpy as np
from PIL import Image
import time

def test_cpu_model():
    print("🧪 CPU에서 DeepLabV3+ 모델 테스트 시작...")
    
    # 1. PyTorch 버전 확인
    print(f"PyTorch 버전: {torch.__version__}")
    print(f"Torchvision 버전: {torchvision.__version__}")
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
    
    # 2. 디바이스 설정
    device = torch.device('cpu')
    print(f"사용 디바이스: {device}")
    
    try:
        # 3. 모델 로딩 테스트
        print("\n📦 모델 로딩 중...")
        start_time = time.time()
        
        # 더 가벼운 ResNet50 기반 모델 사용
        model = torchvision.models.segmentation.deeplabv3_resnet50(
            pretrained=True, progress=True
        )
        model = model.to(device)
        model.eval()
        
        load_time = time.time() - start_time
        print(f"✅ 모델 로딩 완료! (소요시간: {load_time:.2f}초)")
        
        # 4. 더미 이미지로 추론 테스트
        print("\n🖼️ 추론 테스트 중...")
        start_time = time.time()
        
        # 더미 이미지 생성 (작은 크기)
        dummy_image = torch.randn(1, 3, 256, 256).to(device)
        
        with torch.no_grad():
            output = model(dummy_image)['out']
        
        inference_time = time.time() - start_time
        print(f"✅ 추론 완료! (소요시간: {inference_time:.2f}초)")
        print(f"출력 형태: {output.shape}")
        
        # 5. 메모리 사용량 확인
        import psutil
        memory_usage = psutil.virtual_memory()
        print(f"\n💾 메모리 사용량:")
        print(f"  전체: {memory_usage.total / (1024**3):.1f} GB")
        print(f"  사용 중: {memory_usage.used / (1024**3):.1f} GB")
        print(f"  사용률: {memory_usage.percent:.1f}%")
        
        print("\n✅ CPU에서 DeepLabV3+ 모델 정상 작동!")
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cpu_model() 