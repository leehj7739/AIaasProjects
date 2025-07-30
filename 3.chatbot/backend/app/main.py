from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config import settings
from core.app_state import initialize_app_state, cleanup_app_state

app = FastAPI(
    title="Chatbot API",
    description="Neo4j와 벡터 검색을 활용한 챗봇 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행되는 이벤트"""
    success = initialize_app_state()
    if not success:
        print("❌ 애플리케이션 초기화 실패. 서버를 재시작해주세요.")

@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행되는 이벤트"""
    cleanup_app_state()

# 라우터 등록 (순환 import 방지를 위해 여기서 import)
from api.routes import chat, utils
app.include_router(chat.router)
app.include_router(utils.router)

@app.get("/")
async def root():
    return {
        "message": "영화 추천 챗봇 API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "endpoints": {
            "chat": {
                "new_session": "/chat/session/new",
                "send_message": "/chat/send",
                "history": "/chat/history/{session_id}",
                "session_info": "/chat/session/{session_id}/info",
                "sessions": "/chat/sessions",
                "delete_session": "/chat/session/{session_id}",
                "clear_sessions": "/chat/sessions/clear"
            },
            "utils": {
                "database_info": "/utils/database/info",
                "schema_info": "/utils/schema/info",
                "token_usage": "/utils/tokens/usage",
                "cypher_test": "/utils/cypher/test",
                "cypher_examples": "/utils/cypher/examples",
                "detailed_health": "/utils/health/detailed"
            },
            "health": "/health"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
   