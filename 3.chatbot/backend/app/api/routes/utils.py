# app/api/routes/utils.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services.database_service import DatabaseService
from core.schema_manager import SchemaManager
from core.token_manager import TokenManager
from models.chatbot import GraphRAGChatbot
from core.app_state import get_db_service, get_schema_manager, is_initialized

router = APIRouter(prefix="/utils", tags=["utils"])

class CypherTestRequest(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None

class CypherTestResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    execution_time: float
    error_message: Optional[str] = None

@router.get("/database/info")
async def get_database_info():
    """데이터베이스 정보 조회"""
    try:
        if not is_initialized():
            raise HTTPException(status_code=503, detail="애플리케이션이 초기화되지 않았습니다.")
        
        db_service = get_db_service()
        info = db_service.get_database_info()
        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터베이스 정보 조회 실패: {str(e)}")

@router.get("/schema/info")
async def get_schema_info():
    """스키마 정보 조회"""
    try:
        if not is_initialized():
            raise HTTPException(status_code=503, detail="애플리케이션이 초기화되지 않았습니다.")
        
        schema_manager = get_schema_manager()
        schema_info = schema_manager.get_schema_info()
        return {
            "status": "success",
            "data": schema_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스키마 정보 조회 실패: {str(e)}")

@router.get("/tokens/usage")
async def get_token_usage():
    """토큰 사용량 조회"""
    try:
        token_manager = TokenManager()
        usage_info = {
            "daily_usage": token_manager.get_daily_usage(),
            "daily_limit": token_manager.daily_limit,
            "remaining_tokens": token_manager.daily_limit - token_manager.get_daily_usage(),
            "usage_percentage": (token_manager.get_daily_usage() / token_manager.daily_limit) * 100
        }
        return {
            "status": "success",
            "data": usage_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토큰 사용량 조회 실패: {str(e)}")

@router.post("/cypher/test", response_model=CypherTestResponse)
async def test_cypher_query(request: CypherTestRequest):
    """Cypher 쿼리 테스트"""
    import time
    
    try:
        if not is_initialized():
            raise HTTPException(status_code=503, detail="애플리케이션이 초기화되지 않았습니다.")
        
        db_service = get_db_service()
        
        # 쿼리 실행 시간 측정
        start_time = time.time()
        
        with db_service.driver.session() as session:
            if request.parameters:
                result = session.run(request.query, **request.parameters)
            else:
                result = session.run(request.query)
            
            # 결과를 딕셔너리 리스트로 변환
            results = [dict(record) for record in result]
        
        execution_time = time.time() - start_time
        
        return CypherTestResponse(
            success=True,
            results=results,
            execution_time=execution_time,
            error_message=None
        )
        
    except Exception as e:
        return CypherTestResponse(
            success=False,
            results=[],
            execution_time=0.0,
            error_message=str(e)
        )

@router.get("/cypher/examples")
async def get_cypher_examples():
    """Cypher 쿼리 예시 조회"""
    examples = [
        {
            "description": "모든 영화 조회",
            "query": "MATCH (m:Movie) RETURN m.title, m.poster LIMIT 10"
        },
        {
            "description": "특정 배우의 영화 조회",
            "query": "MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE a.name CONTAINS 'Tom Hanks' RETURN m.title, m.poster"
        },
        {
            "description": "액션 장르 영화 조회",
            "query": "MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE g.name = 'Action' RETURN m.title, m.poster LIMIT 10"
        },
        {
            "description": "평점이 높은 영화 조회",
            "query": "MATCH (m:Movie)<-[r:RATED]-(u:User) RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10"
        },
        {
            "description": "특정 영화와 비슷한 영화 추천",
            "query": "MATCH (m:Movie {title: 'The Matrix'})<-[:RATED]-(u:User)-[:RATED]->(rec:Movie) RETURN distinct rec.title, rec.poster LIMIT 10"
        },
        {
            "description": "배우별 영화 수 조회",
            "query": "MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) RETURN a.name, count(m) as movie_count ORDER BY movie_count DESC LIMIT 10"
        },
        {
            "description": "장르별 평균 평점 조회",
            "query": "MATCH (m:Movie)-[:IN_GENRE]->(g:Genre)<-[r:RATED]-(u:User) RETURN g.name, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC"
        }
    ]
    
    return {
        "status": "success",
        "data": examples
    }

@router.get("/health/detailed")
async def get_detailed_health():
    """상세한 시스템 상태 확인"""
    health_info = {
        "database": {"status": "unknown", "message": ""},
        "openai": {"status": "unknown", "message": ""},
        "schema": {"status": "unknown", "message": ""},
        "overall": "unknown"
    }
    
    # 데이터베이스 연결 확인
    try:
        if not is_initialized():
            health_info["database"] = {"status": "error", "message": "애플리케이션이 초기화되지 않음"}
        else:
            db_service = get_db_service()
            test_result = db_service.test_connection()
            health_info["database"] = test_result
    except Exception as e:
        health_info["database"] = {"status": "error", "message": str(e)}
    
    # OpenAI 연결 확인
    try:
        from config.settings import settings
        if settings.openai_api_key:
            health_info["openai"] = {"status": "success", "message": "API Key 설정됨"}
        else:
            health_info["openai"] = {"status": "error", "message": "API Key가 설정되지 않음"}
    except Exception as e:
        health_info["openai"] = {"status": "error", "message": str(e)}
    
    # 스키마 확인
    try:
        if not is_initialized():
            health_info["schema"] = {"status": "error", "message": "애플리케이션이 초기화되지 않음"}
        else:
            schema_manager = get_schema_manager()
            schema_info = schema_manager.get_schema_info()
            health_info["schema"] = {"status": "success", "message": f"스키마 로드됨: {len(schema_info.get('nodes', []))}개 노드, {len(schema_info.get('relationships', []))}개 관계"}
    except Exception as e:
        health_info["schema"] = {"status": "error", "message": str(e)}
    
    # 전체 상태 결정
    all_success = all(info["status"] == "success" for info in health_info.values() if isinstance(info, dict))
    health_info["overall"] = "healthy" if all_success else "unhealthy"
    
    return {
        "status": "success",
        "data": health_info
    }