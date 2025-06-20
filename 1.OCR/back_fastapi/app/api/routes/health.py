from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return {
        "status": "healthy",
        "message": "서버가 정상적으로 실행 중입니다."
    } 