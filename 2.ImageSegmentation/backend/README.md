# 자율주행 시뮬레이션 백엔드 서비스

이 프로젝트는 Unity 자율주행 시뮬레이션을 위한 백엔드 서비스들을 제공합니다.

## 🚀 서비스 목록

### 1. YOLO 객체 검출 서비스 (app.py)
- **포트**: 5000
- **기능**: YOLOv8을 사용한 객체 검출 및 세그멘테이션
- **주요 기능**:
  - 사람, 차량 등 객체 검출
  - 바운딩 박스 좌표 제공
  - 세그멘테이션 마스크 생성
  - 실시간 객체 추적

### 2. DeepLabV3+ 도로 세그멘테이션 서비스 (deeplab_segmentation_services.py)
- **포트**: 5001
- **기능**: DeepLabV3+를 사용한 도로 장면 세그멘테이션
- **주요 기능**:
  - 도로, 차선, 보행자, 신호등 등 픽셀 단위 분할
  - 도로 장면 분석 (안전 점수, 교통 밀도 등)
  - 거리 추정
  - 자율주행 의사결정 지원
  - **GO/STOP 신호** (보행자 검출 시 자동 정지 신호)
  - **바운딩 박스 표시** 및 **좌하단 보행자 정보 표시**

## 📦 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. YOLO 서비스 실행
```bash
python app.py
```
- 웹 인터페이스: http://localhost:5000
- API 엔드포인트: http://localhost:5000/api/detect

### 3. DeepLabV3+ 서비스 실행
```bash
python deeplab_segmentation_services.py
```
- 웹 인터페이스: http://localhost:5001
- API 엔드포인트: http://localhost:5001/api/road_segmentation
- **GO/STOP API**: http://localhost:5001/api/go_stop
- **보행자 검출 API**: http://localhost:5001/detect_person (기존 형식과 동일)

## 🔧 API 사용법

### YOLO API (포트 5000)
```python
import requests

# 이미지 파일로 객체 검출
with open('image.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:5000/api/detect', files=files)
    result = response.json()

# 응답 예시
{
    "success": True,
    "detections": [
        {
            "bbox": [x1, y1, x2, y2],
            "confidence": 0.95,
            "class_name": "person",
            "area": 50000.0
        }
    ],
    "total_objects": 1,
    "person_count": 1
}
```

### DeepLabV3+ API (포트 5001)
```python
import requests

# 이미지 파일로 도로 세그멘테이션
with open('road_image.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:5001/api/road_segmentation', files=files)
    result = response.json()

# 응답 예시
{
    "success": True,
    "status": "stop",  # "go" 또는 "stop"
    "person_count": 1,
    "road_objects": [
        {
            "class_name": "person",
            "bbox": [x1, y1, x2, y2],
            "area": 50000.0
        }
    ],
    "scene_analysis": {
        "pedestrian_count": 1,
        "vehicle_count": 2,
        "traffic_density": 0.3,
        "road_safety_score": 85
    },
    "total_objects": 3
}

# GO/STOP 전용 API
with open('road_image.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:5001/api/go_stop', files=files)
    result = response.json()

# GO/STOP 응답 예시
{
    "success": True,
    "status": "stop",  # "go" 또는 "stop"
    "person_count": 1,
    "visualization_filename": "deeplab_go_stop_20241201_143022_123456.jpg",
    "message": "보행자 1명 감지 - 정지 필요"
}

# 기존 형식과 동일한 보행자 검출 API
with open('road_image.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:5001/detect_person', files=files)
    result = response.json()

# 기존 형식과 동일한 응답
{
    "status": "stop",  # "go" 또는 "stop"
    "person_count": 1
}
```

## 🧪 테스트

### YOLO API 테스트
```bash
python test_api.py
```

### DeepLabV3+ API 테스트
```bash
python test_deeplab_api.py
```

## 🎯 Unity 연동

### Unity에서 API 호출 예시
```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class APIController : MonoBehaviour
{
    public string apiUrl = "http://localhost:5000/api/detect";
    
    public IEnumerator DetectObjects(Texture2D image)
    {
        byte[] imageBytes = image.EncodeToJPG();
        
        WWWForm form = new WWWForm();
        form.AddBinaryData("image", imageBytes, "image.jpg", "image/jpeg");
        
        using (UnityWebRequest request = UnityWebRequest.Post(apiUrl, form))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                string jsonResponse = request.downloadHandler.text;
                // JSON 파싱 및 처리
                ProcessDetectionResult(jsonResponse);
            }
        }
    }
}
```

## 🔍 성능 최적화

### CPU 환경에서 속도 향상
1. **해상도 낮추기**: 입력 이미지 크기를 640x480 이하로 조정
2. **프레임 스킵**: 모든 프레임을 처리하지 않고 2-3프레임마다 처리
3. **경량 모델 사용**: YOLOv8n, YOLOv5n 등 nano 버전 사용
4. **신뢰도 임계값 조정**: 불필요한 검출 제거

### GPU 환경 권장
- NVIDIA GPU가 있다면 자동으로 GPU 사용
- 속도가 10-50배 향상됨

## 📁 파일 구조
```
backend/
├── app.py                          # YOLO 메인 서비스
├── deeplab_segmentation_services.py # DeepLabV3+ 서비스
├── segmentation_services.py        # 기존 세그멘테이션 서비스
├── test_api.py                     # YOLO API 테스트
├── test_deeplab_api.py            # DeepLabV3+ API 테스트
├── requirements.txt                # Python 의존성
├── uploads/                        # 업로드된 이미지
├── results/                        # 처리 결과 이미지
└── templates/                      # 웹 템플릿
```

## 🚨 주의사항

1. **CPU 성능**: CPU만 사용하는 경우 응답 시간이 0.5-1초 정도 소요될 수 있습니다.
2. **메모리 사용량**: GPU 사용 시 VRAM이 충분한지 확인하세요.
3. **네트워크**: Unity와 Python 서버 간 통신이 필요합니다.
4. **포트 충돌**: 5000, 5001 포트가 사용 중이지 않은지 확인하세요.

## 🔧 문제 해결

### 서버 연결 실패
- 서버가 실행 중인지 확인
- 포트 번호 확인
- 방화벽 설정 확인

### 모델 로딩 실패
- PyTorch, torchvision 설치 확인
- GPU 드라이버 업데이트 (GPU 사용 시)

### 메모리 부족
- 이미지 해상도 낮추기
- 배치 크기 줄이기
- 더 가벼운 모델 사용

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. Python 버전 (3.8 이상 권장)
2. CUDA 버전 (GPU 사용 시)
3. 의존성 패키지 버전
4. 시스템 리소스 (CPU, RAM, GPU)
