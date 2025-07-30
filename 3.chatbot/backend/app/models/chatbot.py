"""
메인 챗봇 모델
GraphRAG와 Neo4j를 활용한 영화 추천 챗봇의 핵심 클래스
"""

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from config.settings import settings
from core.token_manager import TokenManager
from core.schema_manager import SchemaManager
from services.intent_classifier import IntentClassifier
from services.cypher_generator import CypherGenerator
from services.response_generator import ResponseGenerator
from services.database_service import DatabaseService
from utils.format_utils import extract_poster_urls

class GraphRAGChatbot:
    """그래프 DB RAG 챗봇 클래스"""
    
    def __init__(self, neo4j_uri=None, neo4j_user=None, neo4j_password=None, 
                 openai_api_key=None, schema_file_path=None, db_service=None, schema_manager=None):
        """그래프 DB RAG 챗봇 초기화"""
        
        # 설정 업데이트
        if neo4j_uri:
            settings.neo4j_uri = neo4j_uri
        if neo4j_user:
            settings.neo4j_user = neo4j_user
        if neo4j_password:
            settings.neo4j_password = neo4j_password
        if openai_api_key:
            settings.openai_api_key = openai_api_key
        if schema_file_path:
            settings.schema_file_path = schema_file_path
        
        # LLM 설정
        self.llm = ChatOpenAI(
            model_name=settings.openai_model, 
            temperature=settings.openai_temperature, 
            api_key=settings.openai_api_key
        )
        
        # 데이터베이스 서비스 초기화 (전역 서비스 사용 또는 새로 생성)
        if db_service:
            self.db_service = db_service
        else:
            self.db_service = DatabaseService()
        
        # 스키마 매니저 초기화 (전역 매니저 사용 또는 새로 생성)
        if schema_manager:
            self.schema_manager = schema_manager
        else:
            self.schema_manager = SchemaManager(
                driver=self.db_service.driver,
                schema_file_path=settings.schema_file_path
            )
        
        # 스키마 로드 또는 추출
        self.schema = self.schema_manager.get_or_load_schema()
        self.neo4j_schema = self.schema_manager.format_schema()
        
        # 서비스들 초기화
        self.intent_classifier = IntentClassifier(self.llm)
        self.cypher_generator = CypherGenerator(self.llm, self.schema)
        self.response_generator = ResponseGenerator(self.llm)
        
        # 토큰 매니저 초기화
        self.token_manager = TokenManager()
        
        # 메시지 히스토리
        self.chat_history = ChatMessageHistory()
        self.session_id = "default"
        
        print(f"✅ 챗봇 인스턴스 초기화 완료")
        print(f"스키마 정보: {self.neo4j_schema[:200]}...")
    
    def check_token_limits(self, user_input):
        """토큰 제한 확인"""
        # 일일 토큰 제한 확인
        if not self.token_manager.check_daily_limit():
            return False, "일일 토큰 사용량 한도를 초과했습니다. 내일 다시 시도해주세요."
        
        # 대화 길이 제한 확인
        if len(self.chat_history.messages) >= settings.max_conversation_length:
            return False, "대화가 너무 길어졌습니다. 새로운 대화를 시작해주세요."
        
        # 입력 토큰 수 확인
        is_valid, token_count = self.token_manager.check_request_limit(user_input)
        if not is_valid:
            return False, f"입력이 너무 깁니다. ({token_count} 토큰) 더 간단하게 질문해주세요."
        
        return True, ""
    
    def process_query(self, user_input):
        """사용자 질문을 처리하고 답변 생성"""
        try:
            # 토큰 제한 확인
            can_process, error_msg = self.check_token_limits(user_input)
            if not can_process:
                return {
                    "answer": error_msg,
                    "cypher_query": "",
                    "search_results": [],
                    "posters": []
                }
            
            # 1. 의도 분류
            intent = self.intent_classifier.classify_intent(user_input)
            
            # 2. 의도에 따른 처리
            if intent == "MOVIE":
                # 영화 관련 질문 처리
                return self._process_movie_query(user_input)
            else:
                # 일반 대화 처리
                return self._process_general_query(user_input)
            
        except Exception as e:
            return {
                "answer": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "cypher_query": "",
                "search_results": [],
                "posters": []
            }
    
    def _process_movie_query(self, user_input):
        """영화 관련 질문 처리"""
        # 1. Cypher 쿼리 생성
        cypher_query = self.cypher_generator.generate_cypher_query(user_input)
        
        # 2. Cypher 쿼리 실행
        search_results = []
        try:
            search_results = self.db_service.execute_query(cypher_query)
        except Exception as e:
            return {
                "answer": f"데이터베이스 쿼리 실행 중 오류가 발생했습니다: {str(e)}",
                "cypher_query": cypher_query,
                "search_results": [],
                "posters": []
            }
        
        # 3. 포스터 URL 추출
        posters = extract_poster_urls(search_results)
        
        # 4. 결과를 한국어로 답변 생성
        answer = self.response_generator.generate_movie_response(
            user_input, search_results, self.chat_history.messages
        )
        
        # 대화 히스토리에 추가
        self.chat_history.add_user_message(user_input)
        self.chat_history.add_ai_message(answer)
        
        # 토큰 사용량 계산 및 추가
        total_tokens = self.token_manager.count_tokens(user_input + answer)
        self.token_manager.add_tokens(total_tokens)
        
        return {
            "answer": answer,
            "cypher_query": cypher_query,
            "search_results": search_results,
            "posters": posters
        }
    
    def _process_general_query(self, user_input):
        """일반 대화 처리"""
        # 일반 대화 응답 생성
        answer = self.response_generator.generate_general_response(
            user_input, self.chat_history.messages
        )
        
        # 대화 히스토리에 추가
        self.chat_history.add_user_message(user_input)
        self.chat_history.add_ai_message(answer)
        
        # 토큰 사용량 계산 및 추가
        total_tokens = self.token_manager.count_tokens(user_input + answer)
        self.token_manager.add_tokens(total_tokens)
        
        return {
            "answer": answer,
            "cypher_query": "",
            "search_results": [],
            "posters": []
        }
    
    def get_chat_history(self):
        """채팅 히스토리 반환"""
        return [msg.content for msg in self.chat_history.messages]
    
    def clear_history(self):
        """채팅 히스토리 초기화"""
        self.chat_history.clear()
    
    def summarize_history(self):
        """대화 히스토리 요약"""
        if len(self.chat_history.messages) <= 10:
            return False
        
        # 토큰 제한 확인
        if not self.token_manager.check_daily_limit():
            return False
        
        summary = self.response_generator.summarize_conversation(self.chat_history.messages)
        
        # 토큰 사용량 추가
        summary_tokens = self.token_manager.count_tokens(summary)
        self.token_manager.add_tokens(summary_tokens)
        
        # 히스토리 초기화 후 요약 추가
        self.chat_history.clear()
        self.chat_history.add_ai_message(summary)
        
        return True
    
    def get_schema_info(self):
        """스키마 정보 반환"""
        return self.schema_manager.get_schema_info()
    
    def get_token_usage(self):
        """토큰 사용량 정보 반환"""
        return self.token_manager.get_usage_stats()
    
    def get_database_info(self):
        """데이터베이스 정보 반환"""
        return self.db_service.get_database_info()
    
    def test_connection(self):
        """데이터베이스 연결 테스트"""
        return self.db_service.test_connection()
    
    def close(self):
        """리소스 정리"""
        if self.db_service:
            self.db_service.close() 