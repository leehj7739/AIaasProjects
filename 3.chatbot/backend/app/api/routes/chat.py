# app/api/routes/chat.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from models.chatbot import GraphRAGChatbot
from utils.session_utils import generate_session_id, validate_session_id, extract_session_info
from core.app_state import get_db_service, get_schema_manager, is_initialized

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    cypher_query: Optional[str] = None
    search_results: List[dict] = []
    posters: List[str] = []
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    message: str
    session_info: dict

# 전역 챗봇 인스턴스 관리
chatbot_instances = {}

@router.post("/session/new", response_model=SessionResponse)
async def create_new_session():
    """새로운 세션 생성"""
    session_id = generate_session_id()
    session_info = extract_session_info(session_id)
    
    return SessionResponse(
        session_id=session_id,
        message="새로운 세션이 생성되었습니다.",
        session_info=session_info
    )

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """챗봇과 대화"""
    try:
        # 애플리케이션이 초기화되었는지 확인
        if not is_initialized():
            raise HTTPException(status_code=503, detail="애플리케이션이 초기화되지 않았습니다. 서버를 재시작해주세요.")
        
        # DB 서비스와 스키마 매니저 가져오기
        db_service = get_db_service()
        schema_manager = get_schema_manager()
        
        # 세션 아이디가 없으면 자동 생성
        if not request.session_id:
            request.session_id = generate_session_id()
        # 세션 아이디 유효성 검사
        elif not validate_session_id(request.session_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 세션 아이디입니다.")
        
        # 세션별 챗봇 인스턴스 관리 (전역 DB 서비스 사용)
        if request.session_id not in chatbot_instances:
            chatbot_instances[request.session_id] = GraphRAGChatbot(
                db_service=db_service,
                schema_manager=schema_manager
            )
        
        chatbot = chatbot_instances[request.session_id]
        result = chatbot.process_query(request.message)
        
        return ChatResponse(
            answer=result["answer"],
            cypher_query=result["cypher_query"],
            search_results=result["search_results"],
            posters=result["posters"],
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """채팅 히스토리 조회"""
    if session_id not in chatbot_instances:
        return {"messages": []}
    
    chatbot = chatbot_instances[session_id]
    return {"messages": chatbot.get_chat_history()}

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """채팅 히스토리 초기화"""
    if session_id in chatbot_instances:
        chatbot_instances[session_id].clear_history()
    return {"message": "히스토리가 초기화되었습니다."}

@router.get("/health")
async def health_check():
    """챗봇 상태 확인"""
    return {"status": "healthy", "active_sessions": len(chatbot_instances)}

@router.get("/sessions")
async def get_active_sessions():
    """활성 세션 목록 조회"""
    sessions_info = {}
    for session_id in chatbot_instances.keys():
        sessions_info[session_id] = extract_session_info(session_id)
    
    return {
        "active_sessions": list(chatbot_instances.keys()),
        "session_count": len(chatbot_instances),
        "sessions_info": sessions_info
    }

@router.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """특정 세션 정보 조회"""
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 세션 아이디입니다.")
    
    session_info = extract_session_info(session_id)
    is_active = session_id in chatbot_instances
    
    return {
        "session_id": session_id,
        "session_info": session_info,
        "is_active": is_active,
        "has_history": is_active and len(chatbot_instances[session_id].get_chat_history()) > 0
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """특정 세션 삭제"""
    if session_id in chatbot_instances:
        del chatbot_instances[session_id]
        return {"message": f"세션 {session_id}가 삭제되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

@router.delete("/sessions/clear")
async def clear_all_sessions():
    """모든 세션 삭제"""
    session_count = len(chatbot_instances)
    chatbot_instances.clear()
    return {"message": f"{session_count}개의 세션이 모두 삭제되었습니다."}