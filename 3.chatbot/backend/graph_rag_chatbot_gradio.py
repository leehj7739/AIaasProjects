import os
import gradio as gr
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from neo4j_genai.retrievers import Text2CypherRetriever
from neo4j_genai.generation import GraphRAG
from neo4j_genai.llm import OpenAILLM
import json
from datetime import datetime
import re
import tiktoken

# 환경변수 로드
load_dotenv()

# 토큰 제한 설정
MAX_TOKENS_PER_REQUEST = 4000  # 요청당 최대 토큰 수
MAX_TOKENS_PER_DAY = 50000     # 일일 최대 토큰 수
MAX_CONVERSATION_LENGTH = 20   # 대화 최대 길이

class TokenManager:
    """토큰 사용량을 관리하는 클래스"""
    
    def __init__(self):
        self.daily_tokens = 0
        self.last_reset_date = datetime.now().date()
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    
    def count_tokens(self, text):
        """텍스트의 토큰 수를 계산"""
        try:
            return len(self.encoding.encode(text))
        except:
            # tiktoken이 실패하면 대략적인 추정 (1 토큰 ≈ 4 문자)
            return len(text) // 4
    
    def check_daily_limit(self):
        """일일 토큰 제한 확인"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_tokens = 0
            self.last_reset_date = current_date
        
        return self.daily_tokens < MAX_TOKENS_PER_DAY
    
    def add_tokens(self, token_count):
        """토큰 사용량 추가"""
        self.daily_tokens += token_count
    
    def get_daily_usage(self):
        """일일 토큰 사용량 반환"""
        return self.daily_tokens
    
    def get_remaining_tokens(self):
        """남은 토큰 수 반환"""
        return max(0, MAX_TOKENS_PER_DAY - self.daily_tokens)

# 전역 토큰 매니저
token_manager = TokenManager()

def get_node_datatype(value):
    """입력된 노드 Value의 데이터 타입을 반환하는 함수"""
    if isinstance(value, str):
        return "STRING"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "FLOAT"
    elif isinstance(value, bool):
        return "BOOLEAN"
    elif isinstance(value, list):
        return f"LIST[{get_node_datatype(value[0])}]" if value else "LIST"
    else:
        return "UNKNOWN"

def load_schema_from_file(schema_file_path="guide/movie_schema.json"):
    """스키마 파일에서 로드하는 함수"""
    try:
        if os.path.exists(schema_file_path):
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
                print(f"✅ 스키마 파일에서 로드됨: {schema_file_path}")
                return schema_data.get("schema", None)
        else:
            print(f"⚠️ 스키마 파일이 없습니다: {schema_file_path}")
            return None
    except Exception as e:
        print(f"❌ 스키마 파일 로드 실패: {e}")
        return None

def get_schema(driver):
    """Graph DB의 정보를 받아 노드 및 관계의 프로퍼티를 추출하고 스키마 딕셔너리를 반환하는 함수"""
    try:
        with driver.session() as session:
            # 노드 프로퍼티 및 타입 추출 (수정된 버전)
            node_query = """
            MATCH (n)
            WITH DISTINCT labels(n) AS node_labels, keys(n) AS property_keys
            UNWIND node_labels AS label
            UNWIND property_keys AS key
            WITH label, key
            MATCH (n)
            WHERE ANY(l IN labels(n) WHERE l = label) AND n[key] IS NOT NULL
            RETURN label, key, n[key] AS sample_value
            LIMIT 1
            """
            nodes = session.run(node_query)

            # 관계 프로퍼티 및 타입 추출 (수정된 버전)
            rel_query = """
            MATCH ()-[r]->()
            WITH DISTINCT type(r) AS rel_type, keys(r) AS property_keys
            UNWIND property_keys AS key
            WITH rel_type, key
            MATCH ()-[r]->()
            WHERE type(r) = rel_type AND r[key] IS NOT NULL
            RETURN rel_type, key, r[key] AS sample_value
            LIMIT 1
            """
            relationships = session.run(rel_query)

            # 관계 유형 및 방향 추출 (수정된 버전)
            rel_direction_query = """
            MATCH (a)-[r]->(b)
            WITH DISTINCT labels(a) AS start_labels, type(r) AS rel_type, labels(b) AS end_labels
            UNWIND start_labels AS start_label
            UNWIND end_labels AS end_label
            RETURN start_label, rel_type, end_label
            ORDER BY start_label, rel_type, end_label
            """
            rel_directions = session.run(rel_direction_query)

            # 스키마 딕셔너리 생성
            schema = {"nodes": {}, "relationships": {}, "relations": []}

            for record in nodes:
                label = record["label"]
                key = record["key"]
                sample_value = record["sample_value"]
                inferred_type = get_node_datatype(sample_value)
                if label not in schema["nodes"]:
                    schema["nodes"][label] = {}
                schema["nodes"][label][key] = inferred_type

            for record in relationships:
                rel_type = record["rel_type"]
                key = record["key"]
                sample_value = record["sample_value"]
                inferred_type = get_node_datatype(sample_value)
                if rel_type not in schema["relationships"]:
                    schema["relationships"][rel_type] = {}
                schema["relationships"][rel_type][key] = inferred_type

            for record in rel_directions:
                start_label = record["start_label"]
                rel_type = record["rel_type"]
                end_label = record["end_label"]
                schema["relations"].append(f"(:{start_label})-[:{rel_type}]->(:{end_label})")

            return schema
    except Exception as e:
        print(f"스키마 추출 실패: {e}")
        return None

def get_or_load_schema(driver, schema_file_path="guide/movie_schema.json"):
    """스키마를 파일에서 로드하거나 데이터베이스에서 추출"""
    try:
        # 먼저 파일에서 로드 시도
        schema = load_schema_from_file(schema_file_path)
        if schema:
            print(f"✅ 스키마를 파일에서 로드했습니다: {schema_file_path}")
            return schema
    except Exception as e:
        print(f"⚠️ 스키마 파일 로드 실패: {e}")
    
    try:
        # 파일이 없거나 로드 실패시 데이터베이스에서 추출
        print("🔄 데이터베이스에서 스키마 추출 중...")
        schema = get_schema(driver)
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(schema_file_path), exist_ok=True)
        
        # 스키마를 파일로 저장
        with open(schema_file_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 스키마를 데이터베이스에서 추출하여 저장했습니다: {schema_file_path}")
        return schema
        
    except Exception as e:
        print(f"❌ 스키마 추출 실패: {e}")
        # 기본 스키마 반환
        print("🔄 기본 스키마 사용")
        return {
            "nodes": {
                "Movie": {"title": "string", "year": "integer", "poster": "string"},
                "Actor": {"name": "string"},
                "Director": {"name": "string"},
                "Genre": {"name": "string"},
                "User": {"name": "string"}
            },
            "relationships": {
                "ACTED_IN": {},
                "DIRECTED": {},
                "IN_GENRE": {},
                "RATED": {"rating": "float"}
            },
            "relations": [
                "(Actor)-[:ACTED_IN]->(Movie)",
                "(Director)-[:DIRECTED]->(Movie)",
                "(Movie)-[:IN_GENRE]->(Genre)",
                "(User)-[:RATED]->(Movie)"
            ]
        }

def format_schema(schema):
    """스키마 딕셔너리를 LLM에 제공하기 위해 원하는 형태로 formatting 하는 함수"""
    if not schema:
        return ""
    
    result = []

    # 노드 프로퍼티 출력
    result.append("Node properties:")
    for label, properties in schema["nodes"].items():
        props = ", ".join(f"{k}: {v}" for k, v in properties.items())
        result.append(f"{label} {{{{{props}}}}}")  # 이중 중괄호로 이스케이프

    # 관계 프로퍼티 출력
    result.append("Relationship properties:")
    for rel_type, properties in schema["relationships"].items():
        props = ", ".join(f"{k}: {v}" for k, v in properties.items())
        result.append(f"{rel_type} {{{{{props}}}}}")  # 이중 중괄호로 이스케이프

    # 관계 출력
    result.append("The relationships:")
    for relation in schema["relations"]:
        result.append(relation)

    return "\n".join(result)

def generate_examples_from_schema(schema):
    """스키마를 기반으로 예시 쿼리 생성"""
    examples = []
    
    if not schema:
        # 기본 예시 (스키마 추출 실패시)
        return [
            "USER INPUT: 'Which actors starred in the Toy Story?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE m.title = 'Toy Story' RETURN a.name",
            "USER INPUT: 'What is the average user rating for Toy Story?' QUERY: MATCH (u:User)-[r:RATED]->(m:Movie) WHERE m.title = 'Toy Story' RETURN AVG(r.rating)",
            "USER INPUT: 'What movies did Tom Hanks star in?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE a.name = 'Tom Hanks' RETURN m.title",
            "USER INPUT: 'Recommend movies similar to The Matrix' QUERY: MATCH (m:Movie {title: 'The Matrix'})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec:Movie) RETURN rec.title LIMIT 10"
        ]
    
    # 노드 기반 예시 생성
    for node_label in schema["nodes"].keys():
        if node_label.lower() in ['movie', 'film']:
            examples.append(f"USER INPUT: 'Show me all movies' QUERY: MATCH (m:{node_label}) RETURN m.title LIMIT 10")
        elif node_label.lower() in ['actor', 'person']:
            examples.append(f"USER INPUT: 'Show me all actors' QUERY: MATCH (a:{node_label}) RETURN a.name LIMIT 10")
        elif node_label.lower() in ['genre']:
            examples.append(f"USER INPUT: 'Show me all genres' QUERY: MATCH (g:{node_label}) RETURN g.name LIMIT 10")
        elif node_label.lower() in ['director']:
            examples.append(f"USER INPUT: 'Show me all directors' QUERY: MATCH (d:{node_label}) RETURN d.name LIMIT 10")
        elif node_label.lower() in ['user']:
            examples.append(f"USER INPUT: 'Show me all users' QUERY: MATCH (u:{node_label}) RETURN u.name LIMIT 10")
    
    # 관계 기반 예시 생성
    for relation in schema["relations"]:
        # ACTED_IN 관계 예시
        if "ACTED_IN" in relation:
            examples.append(f"USER INPUT: 'Which actors starred in a specific movie?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE m.title = $movie_title RETURN a.name")
        
        # RATED 관계 예시
        if "RATED" in relation:
            examples.append(f"USER INPUT: 'What is the average rating for a movie?' QUERY: MATCH (u:User)-[r:RATED]->(m:Movie) WHERE m.title = $movie_title RETURN AVG(r.rating)")
        
        # IN_GENRE 관계 예시
        if "IN_GENRE" in relation:
            examples.append(f"USER INPUT: 'What genre is this movie?' QUERY: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE m.title = $movie_title RETURN g.name")
        
        # DIRECTED 관계 예시
        if "DIRECTED" in relation:
            examples.append(f"USER INPUT: 'Who directed this movie?' QUERY: MATCH (d:Director)-[:DIRECTED]->(m:Movie) WHERE m.title = $movie_title RETURN d.name")
    
    # 한국어-영어 번역 예시 추가
    examples.extend([
        "USER INPUT: '액션 영화 추천해줘' QUERY: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE g.name = 'Action' RETURN m.title, m.poster LIMIT 10",
        "USER INPUT: '로맨스 영화 중에서 평점이 높은 것들은?' QUERY: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE g.name = 'Romance' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10",
        "USER INPUT: 'Tom Hanks가 출연한 영화는?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE a.name = 'Tom Hanks' RETURN m.title, m.poster",
        "USER INPUT: 'The Matrix와 비슷한 영화는?' QUERY: MATCH (m:Movie {title: 'The Matrix'})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec:Movie) RETURN rec.title, rec.poster LIMIT 10",
        "USER INPUT: 'Leonardo DiCaprio의 최고 작품은?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie), (u:User)-[r:RATED]->(m) WHERE a.name = 'Leonardo DiCaprio' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 5",
        "USER INPUT: '스릴러 장르 영화들 보여줘' QUERY: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE g.name = 'Thriller' RETURN m.title, m.poster LIMIT 10",
        "USER INPUT: '애니메이션 영화 평점순으로 추천해줘' QUERY: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE g.name = 'Animation' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10",
        "USER INPUT: '조니뎁 영화 평점 높은거 추천해줘' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)<-[r:RATED]-(u:User) WHERE a.name = 'Johnny Depp' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10",
        "USER INPUT: '로맨스 장르 영화 평점순으로 추천해줘' QUERY: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE g.name = 'Romance' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10",
        "USER INPUT: '톰 행크스 영화 평점순으로 추천해줘' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)<-[r:RATED]-(u:User) WHERE a.name = 'Tom Hanks' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10",
        "USER INPUT: '조니뎁이 출연한 애니메이션 영화 평점순으로 추천해줘' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE a.name = 'Johnny Depp' AND g.name = 'Animation' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 10"
    ])
    
    # 기본 예시 추가 (최소 4개 보장)
    if len(examples) < 4:
        examples.extend([
            "USER INPUT: 'Which actors starred in the Toy Story?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE m.title = 'Toy Story' RETURN a.name",
            "USER INPUT: 'What is the average user rating for Toy Story?' QUERY: MATCH (u:User)-[r:RATED]->(m:Movie) WHERE m.title = 'Toy Story' RETURN AVG(r.rating)",
            "USER INPUT: 'What movies did Tom Hanks star in?' QUERY: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE a.name = 'Tom Hanks' RETURN m.title",
            "USER INPUT: 'Recommend movies similar to The Matrix' QUERY: MATCH (m:Movie {title: 'The Matrix'})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec:Movie) RETURN rec.title LIMIT 10"
        ])
    
    return examples[:12]  # 최대 12개 예시로 제한 (한국어 예시 추가로 인해 증가)

class GraphRAGChatbot:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, openai_api_key, schema_file_path="guide/movie_schema.json"):
        """그래프 DB RAG 챗봇 초기화"""
        self.driver = GraphDatabase.driver(neo4j_uri, auth=basic_auth(neo4j_user, neo4j_password))
        
        # LLM 설정
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini", 
            temperature=0, 
            api_key=openai_api_key
        )
        
        # 스키마 로드 또는 추출
        self.schema = get_or_load_schema(self.driver, schema_file_path)
        self.examples = generate_examples_from_schema(self.schema)
        self.neo4j_schema = format_schema(self.schema)
        
        print(f"생성된 예시 수: {len(self.examples)}")
        print(f"스키마 정보: {self.neo4j_schema[:200]}...")
        
        # Cypher 쿼리 생성 프롬프트
        self.cypher_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"""당신은 Neo4j Cypher 쿼리 생성 전문가입니다.
                사용자의 자연어 질문을 정확한 Cypher 쿼리로 변환해주세요.
                
                데이터베이스 스키마:
                {self.neo4j_schema}
                
                예시:
                {chr(10).join(self.examples[:6])}
                
                ⚠️ 중요 규칙: 
                1. 한국어 키워드를 적절한 영어로 번역하여 사용
                   - 영화 제목: "토이스토리" → "Toy Story"
                   - 배우 이름: "톰 행크스" → "Tom Hanks"
                   - 장르명: "액션" → "Action", "로맨스" → "Romance"
                   - 감독명: "크리스토퍼 놀란" → "Christopher Nolan"
                
                2. 쿼리 작성 규칙:
                   - 영화 검색: MATCH (m:Movie) WHERE m.title CONTAINS '키워드' RETURN m.title, m.poster
                   - 배우 검색: MATCH (a:Actor) WHERE a.name CONTAINS '이름' RETURN a.name
                   - 장르별 영화: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE g.name = '장르명' RETURN m.title, m.poster
                   - 배우의 영화: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE a.name = '배우명' RETURN m.title, m.poster
                   - 장르별 평점순 정렬: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE g.name = '장르명' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC
                   - 배우별 평점순 정렬: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)<-[r:RATED]-(u:User) WHERE a.name = '배우명' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC
                   - 배우+장르별 평점순 정렬: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE a.name = '배우명' AND g.name = '장르명' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC
                
                3. 응답 형식:
                   - 쿼리만 반환하고 설명은 하지 마세요
                   - 쿼리는 한 줄로 작성하세요
                   - 세미콜론(;)은 제외하세요
                
                4. 일반적인 쿼리 패턴:
                   - 영화 추천: LIMIT 10 추가
                   - 평점 계산: AVG(r.rating) 사용
                   - 정렬: ORDER BY 사용
                   - 필터링: WHERE 절 사용"""
            ),
            ("human", "{input}")
        ])
        
        # Cypher 쿼리 생성 체인
        self.cypher_chain = self.cypher_prompt | self.llm
        
        # 의도 분류 프롬프트
        self.intent_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """당신은 사용자의 의도를 분류하는 전문가입니다.
                사용자의 질문이 영화 데이터베이스와 관련된 것인지, 일반적인 대화인지 판단해주세요.
                
                영화 관련 질문의 예시:
                - 영화 추천, 영화 정보, 배우 정보, 감독 정보
                - 장르별 영화, 평점, 개봉년도, 영화 제목
                - "Tom Hanks 영화", "액션 영화 추천", "The Matrix 비슷한 영화"
                - "평점 높은 영화", "2020년 영화", "로맨스 영화"
                
                일반 대화의 예시:
                - 인사, 자기소개, 이름 묻기, 날씨, 일상 대화
                - "안녕하세요", "내 이름은 홍길동이야", "오늘 날씨 어때?"
                - "너는 누구야?", "잘 지내?", "고마워"
                
                응답 형식:
                - 영화 관련: "MOVIE"
                - 일반 대화: "GENERAL"
                - 확실하지 않으면: "GENERAL"
                
                분류만 반환하고 설명은 하지 마세요."""
            ),
            ("human", "{input}")
        ])
        
        # 의도 분류 체인
        self.intent_chain = self.intent_prompt | self.llm
        
        # 일반 대화 프롬프트
        self.general_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
                사용자와 자연스럽게 대화하세요.
                대화 히스토리를 참고하여 맥락을 유지하세요.
                사용자가 이전에 말한 이름이나 정보를 기억하고 활용하세요.
                친근하고 따뜻한 톤으로 답변해주세요."""
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}")
        ])
        
        # 일반 대화 체인
        self.general_chain = self.general_prompt | self.llm
        
        # 메시지 히스토리
        self.chat_history = ChatMessageHistory()
        self.session_id = "default"
    
    def get_schema_info(self):
        """스키마 정보 반환"""
        return {
            "schema": self.schema,
            "formatted_schema": self.neo4j_schema,
            "examples": self.examples
        }
    
    def check_token_limits(self, user_input):
        """토큰 제한 확인"""
        global token_manager
        
        # 일일 토큰 제한 확인
        if not token_manager.check_daily_limit():
            return False, "일일 토큰 사용량 한도를 초과했습니다. 내일 다시 시도해주세요."
        
        # 대화 길이 제한 확인
        if len(self.chat_history.messages) >= MAX_CONVERSATION_LENGTH:
            return False, "대화가 너무 길어졌습니다. 새로운 대화를 시작해주세요."
        
        # 입력 토큰 수 확인
        input_tokens = token_manager.count_tokens(user_input)
        if input_tokens > MAX_TOKENS_PER_REQUEST:
            return False, f"입력이 너무 깁니다. ({input_tokens} 토큰) 더 간단하게 질문해주세요."
        
        return True, ""
    
    def process_query(self, user_input):
        """사용자 질문을 처리하고 답변 생성"""
        global token_manager
        
        try:
            # 토큰 제한 확인
            can_process, error_msg = self.check_token_limits(user_input)
            if not can_process:
                return {
                    "answer": error_msg,
                    "cypher_query": "",
                    "search_results": []
                }
            
            # 1. 의도 분류
            intent_response = self.intent_chain.invoke({"input": user_input})
            intent = intent_response.content.strip().upper()
            
            print(f"의도 분류: {intent} - 입력: {user_input}")
            
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
                "search_results": []
            }
    
    def _process_movie_query(self, user_input):
        """영화 관련 질문 처리"""
        global token_manager
        
        # 1. Cypher 쿼리 생성
        cypher_response = self.cypher_chain.invoke({"input": user_input})
        cypher_query = cypher_response.content.strip()
        
        # 2. Cypher 쿼리 실행
        search_results = []
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query)
                search_results = [dict(record) for record in result]
        except Exception as e:
            return {
                "answer": f"데이터베이스 쿼리 실행 중 오류가 발생했습니다: {str(e)}",
                "cypher_query": cypher_query,
                "search_results": []
            }
        
        # 3. 결과를 한국어로 답변 생성
        answer_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """당신은 영화 데이터베이스를 기반으로 한 도우미입니다.
                사용자의 질문에 대해 검색 결과를 바탕으로 친근하고 자연스럽게 한국어로 답변해주세요.
                대화 히스토리를 참고하여 맥락을 유지하세요.
                사용자가 이전에 말한 이름이나 선호도 등을 기억하고 활용하세요.
                영화 추천 시에는 이유도 함께 설명해주세요.
                답변은 간결하고 명확하게 해주세요."""
            ),
            ("placeholder", "{chat_history}"),
            ("human", "사용자 질문: {question}\n\n검색 결과: {results}\n\n위 결과를 바탕으로 답변해주세요.")
        ])
        
        answer_chain = answer_prompt | self.llm
        answer_response = answer_chain.invoke({
            "chat_history": self.chat_history.messages,
            "question": user_input,
            "results": str(search_results)
        })
        
        # 대화 히스토리에 추가
        self.chat_history.add_user_message(user_input)
        self.chat_history.add_ai_message(answer_response.content)
        
        # 토큰 사용량 계산 및 추가
        total_tokens = token_manager.count_tokens(user_input + answer_response.content)
        token_manager.add_tokens(total_tokens)
        
        return {
            "answer": answer_response.content,
            "cypher_query": cypher_query,
            "search_results": search_results
        }
    
    def _process_general_query(self, user_input):
        """일반 대화 처리"""
        global token_manager
        
        # 일반 대화 체인 실행
        general_response = self.general_chain.invoke({
            "chat_history": self.chat_history.messages,
            "input": user_input
        })
        
        # 대화 히스토리에 추가
        self.chat_history.add_user_message(user_input)
        self.chat_history.add_ai_message(general_response.content)
        
        # 토큰 사용량 계산 및 추가
        total_tokens = token_manager.count_tokens(user_input + general_response.content)
        token_manager.add_tokens(total_tokens)
        
        return {
            "answer": general_response.content,
            "cypher_query": "",
            "search_results": []
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
        
        global token_manager
        
        # 토큰 제한 확인
        if not token_manager.check_daily_limit():
            return False
        
        summarization_prompt = ChatPromptTemplate.from_messages([
            ("placeholder", "{chat_history}"),
            (
                "user",
                "위의 대화 내용을 핵심만 요약해주세요. 사용자의 선호도나 중요한 정보는 포함해주세요.",
            ),
        ])
        
        summarization_chain = summarization_prompt | self.llm
        summary = summarization_chain.invoke({"chat_history": self.chat_history.messages})
        
        # 토큰 사용량 추가
        summary_tokens = token_manager.count_tokens(summary.content)
        token_manager.add_tokens(summary_tokens)
        
        # 히스토리 초기화 후 요약 추가
        self.chat_history.clear()
        self.chat_history.add_ai_message(summary.content)
        
        return True
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.driver:
            self.driver.close()

# 전역 챗봇 인스턴스
chatbot_instance = None

def initialize_chatbot(neo4j_uri, neo4j_user, neo4j_password, openai_api_key):
    """챗봇 초기화"""
    global chatbot_instance
    try:
        chatbot_instance = GraphRAGChatbot(neo4j_uri, neo4j_user, neo4j_password, openai_api_key)
        return "✅ 챗봇이 성공적으로 초기화되었습니다!"
    except Exception as e:
        return f"❌ 챗봇 초기화 실패: {str(e)}"

def chat_with_bot(message, history):
    """Gradio 채팅 함수"""
    global chatbot_instance
    
    if chatbot_instance is None:
        return "챗봇이 초기화되지 않았습니다. 먼저 설정을 완료해주세요.", history
    
    try:
        # 챗봇 처리
        response = chatbot_instance.process_query(message)
        
        # 히스토리 요약 필요시 수행
        chatbot_instance.summarize_history()
        
        # Gradio 히스토리 형식으로 변환 (기본 튜플 형식)
        history.append((message, response["answer"]))
        
        return "", history
        
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        history.append((message, error_msg))
        return "", history

def clear_chat_history():
    """채팅 히스토리 초기화"""
    global chatbot_instance
    if chatbot_instance:
        chatbot_instance.clear_history()
    return []  # 빈 리스트 반환 (새로운 형식)

def get_cypher_query(message):
    """Cypher 쿼리 확인"""
    global chatbot_instance
    if chatbot_instance is None:
        return "챗봇이 초기화되지 않았습니다."
    
    try:
        response = chatbot_instance.process_query(message)
        return response.get("cypher_query", "쿼리를 생성할 수 없습니다.")
    except Exception as e:
        return f"오류: {str(e)}"

def get_database_info():
    """데이터베이스 정보 확인"""
    global chatbot_instance
    if chatbot_instance is None:
        return "챗봇이 초기화되지 않았습니다."
    
    try:
        with chatbot_instance.driver.session() as session:
            # 영화 수 확인
            movie_count = session.run("MATCH (m:Movie) RETURN count(m) as count").single()["count"]
            # 배우 수 확인
            actor_count = session.run("MATCH (a:Actor) RETURN count(a) as count").single()["count"]
            # 장르 수 확인
            genre_count = session.run("MATCH (g:Genre) RETURN count(g) as count").single()["count"]
            
            return f"""
            📊 데이터베이스 정보:
            - 영화: {movie_count}개
            - 배우: {actor_count}명
            - 장르: {genre_count}개
            """
    except Exception as e:
        return f"데이터베이스 정보 조회 실패: {str(e)}"

def get_schema_info():
    """스키마 정보 확인"""
    global chatbot_instance
    if chatbot_instance is None:
        return "챗봇이 초기화되지 않았습니다."
    
    try:
        schema_info = chatbot_instance.get_schema_info()
        return f"""
        📋 스키마 정보:
        
        생성된 예시 수: {len(schema_info['examples'])}
        
        스키마:
        {schema_info['formatted_schema']}
        """
    except Exception as e:
        return f"스키마 정보 조회 실패: {str(e)}"

def get_token_usage():
    """토큰 사용량 정보 확인"""
    global token_manager
    return f"""
    🔢 토큰 사용량 정보:
    
    일일 사용량: {token_manager.get_daily_usage():,} / {MAX_TOKENS_PER_DAY:,} 토큰
    남은 토큰: {token_manager.get_remaining_tokens():,} 토큰
    요청당 최대: {MAX_TOKENS_PER_REQUEST:,} 토큰
    대화 최대 길이: {MAX_CONVERSATION_LENGTH} 메시지
    """

def test_neo4j_connection(neo4j_uri, neo4j_user, neo4j_password):
    """Neo4j 연결 테스트"""
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=basic_auth(neo4j_user, neo4j_password))
        with driver.session() as session:
            # 기본 쿼리 테스트
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()["total_nodes"]
            
            # 영화 노드 수 확인
            result = session.run("MATCH (m:Movie) RETURN count(m) as movie_count")
            movie_count = result.single()["movie_count"]
            
            # 배우 노드 수 확인
            result = session.run("MATCH (a:Actor) RETURN count(a) as actor_count")
            actor_count = result.single()["actor_count"]
            
            driver.close()
            
            return {
                "status": "success",
                "message": f"✅ Neo4j 연결 성공! 총 노드: {total_nodes}, 영화: {movie_count}, 배우: {actor_count}",
                "total_nodes": total_nodes,
                "movie_count": movie_count,
                "actor_count": actor_count
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Neo4j 연결 실패: {str(e)}",
            "total_nodes": 0,
            "movie_count": 0,
            "actor_count": 0
        }

def test_cypher_query(cypher_query, neo4j_uri, neo4j_user, neo4j_password):
    """Cypher 쿼리 테스트"""
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=basic_auth(neo4j_user, neo4j_password))
        with driver.session() as session:
            result = session.run(cypher_query)
            results = [dict(record) for record in result]
            driver.close()
            
            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": [],
            "count": 0
        }

def test_neo4j_connection_wrapper(neo4j_uri, neo4j_user, neo4j_password):
    """Neo4j 연결 테스트 (Gradio 래퍼)"""
    result = test_neo4j_connection(neo4j_uri, neo4j_user, neo4j_password)
    return result["message"]

# Gradio 인터페이스 생성
def create_interface():
    with gr.Blocks(title="영화 추천 챗봇", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎬 영화 추천 챗봇")
        gr.Markdown("Neo4j 그래프 데이터베이스와 RAG를 활용한 영화 추천 시스템")
        
        with gr.Tab("설정"):
            gr.Markdown("## 🔧 챗봇 설정")
            
            with gr.Row():
                with gr.Column():
                    neo4j_uri = gr.Textbox(
                        label="Neo4j URI",
                        value="neo4j://54.152.35.230:7687",
                        placeholder="neo4j://54.152.35.230:7687"
                    )
                    neo4j_user = gr.Textbox(
                        label="Neo4j 사용자명",
                        value="neo4j",
                        placeholder="neo4j"
                    )
                    neo4j_password = gr.Textbox(
                        label="Neo4j 비밀번호",
                        value="designations-oscillations-convention",
                        placeholder="designations-oscillations-convention",
                        type="password"
                    )
                    openai_api_key = gr.Textbox(
                        label="OpenAI API Key",
                        value=os.getenv("OPENAI_API_KEY", ""),
                        placeholder="sk-...",
                        type="password"
                    )
                
                with gr.Column():
                    init_btn = gr.Button("🚀 챗봇 초기화", variant="primary")
                    test_connection_btn = gr.Button("🔍 연결 테스트", variant="secondary")
                
                init_status = gr.Textbox(
                    label="초기화 상태",
                    value="챗봇을 초기화해주세요.",
                    interactive=False
                )
                
                test_status = gr.Textbox(
                    label="연결 테스트 결과",
                    value="연결을 테스트해주세요.",
                    interactive=False
                )
            
            init_btn.click(
                fn=initialize_chatbot,
                inputs=[neo4j_uri, neo4j_user, neo4j_password, openai_api_key],
                outputs=init_status
            )
            
            test_connection_btn.click(
                fn=test_neo4j_connection_wrapper,
                inputs=[neo4j_uri, neo4j_user, neo4j_password],
                outputs=test_status
            )
        
        with gr.Tab("채팅"):
            gr.Markdown("## 💬 영화 추천 챗봇과 대화하기")
            
            with gr.Row():
                # 왼쪽: 채팅 인터페이스
                with gr.Column(scale=2):
                    # 채팅 인터페이스
                    chatbot = gr.Chatbot(
                        label="영화 추천 챗봇",
                        height=400,
                        type="messages"
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="질문 입력",
                            placeholder="영화에 대해 무엇이든 물어보세요!",
                            scale=4
                        )
                        submit_btn = gr.Button("전송", variant="primary", scale=1)
                    
                    # 예시 질문들
                    with gr.Row():
                        gr.Markdown("**예시 질문:**")
                    
                    with gr.Row():
                        example_btns = [
                            gr.Button("Tom Hanks 영화", size="sm"),
                            gr.Button("액션 영화 추천", size="sm"),
                            gr.Button("The Matrix 비슷한 영화", size="sm"),
                            gr.Button("로맨스 평점 높은 영화", size="sm"),
                            gr.Button("Leonardo DiCaprio 최고작", size="sm")
                        ]
                    
                    # 대화 초기화 버튼
                    with gr.Row():
                        clear_btn = gr.Button("대화 히스토리 초기화", variant="secondary")
                
                # 오른쪽: Cypher 쿼리 및 조회 내역
                with gr.Column(scale=1):
                    # 1. 작성된 Cypher 쿼리
                    gr.Markdown("### 🔍 생성된 Cypher 쿼리")
                    cypher_display = gr.Code(
                        label="최근 Cypher 쿼리",
                        language="sql",
                        interactive=False,
                        lines=8
                    )
                    
                    # 2. Cypher 조회 내역
                    gr.Markdown("### 📊 조회 결과")
                    results_display = gr.JSON(
                        label="최근 조회 결과",
                        height=150
                    )
                    
                    # 3. 영화 포스터 이미지
                    gr.Markdown("### 🎬 영화 포스터")
                    poster_display = gr.Gallery(
                        label="영화 포스터",
                        height=200,
                        columns=3,
                        rows=2,
                        object_fit="contain"
                    )
            
            # 이벤트 핸들러
            def user_input(message, history):
                if not message.strip():
                    return "", history, "", {}, []
                
                global chatbot_instance
                if chatbot_instance is None:
                    return "", history + [{"role": "user", "content": message}, {"role": "assistant", "content": "챗봇이 초기화되지 않았습니다. 먼저 설정을 완료해주세요."}], "", {}, []
                
                try:
                    response = chatbot_instance.process_query(message)
                    
                    # 포스터 이미지 추출
                    posters = []
                    if response.get("search_results"):
                        for result in response.get("search_results", []):
                            # 다양한 필드에서 포스터 URL 찾기
                            poster_url = None
                            if "poster" in result:
                                poster_url = result["poster"]
                            elif "m.poster" in result:
                                poster_url = result["m.poster"]
                            elif "movie.poster" in result:
                                poster_url = result["movie.poster"]
                            
                            if poster_url and poster_url != "N/A" and poster_url != "":
                                # 영화 제목도 함께 저장
                                title = result.get("title", result.get("m.title", result.get("movie.title", "Unknown")))
                                posters.append((poster_url, title))
                    
                    return "", history + [{"role": "user", "content": message}, {"role": "assistant", "content": response["answer"]}], response.get("cypher_query", ""), response.get("search_results", []), posters
                except Exception as e:
                    return "", history + [{"role": "user", "content": message}, {"role": "assistant", "content": f"오류가 발생했습니다: {str(e)}"}], "", {}, []
            
            def clear_history():
                global chatbot_instance
                if chatbot_instance:
                    chatbot_instance.clear_history()
                return [], "", {}, []
            
            # 이벤트 연결
            submit_btn.click(
                fn=user_input,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, cypher_display, results_display, poster_display]
            )
            
            msg.submit(
                fn=user_input,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, cypher_display, results_display, poster_display]
            )
            
            clear_btn.click(
                fn=clear_history,
                outputs=[chatbot, cypher_display, results_display, poster_display]
            )
            
            # 예시 버튼들
            for i, btn in enumerate(example_btns):
                examples = [
                    "Tom Hanks가 출연한 영화는?",
                    "액션 영화 추천해줘",
                    "The Matrix와 비슷한 영화는?",
                    "로맨스 영화 중에서 평점이 높은 것들은?",
                    "Leonardo DiCaprio의 최고 작품은?"
                ]
                btn.click(
                    fn=lambda x: x,
                    inputs=[],
                    outputs=msg,
                    js=f"() => '{examples[i]}'"
                )
        
        with gr.Tab("쿼리 확인"):
            gr.Markdown("## 🔍 Cypher 쿼리 확인")
            gr.Markdown("질문에 대해 생성되는 Cypher 쿼리를 확인할 수 있습니다.")
            
            query_input = gr.Textbox(
                label="질문 입력",
                placeholder="Tom Hanks가 출연한 영화는?"
            )
            query_button = gr.Button("쿼리 확인", variant="primary")
            query_output = gr.Code(
                label="생성된 Cypher 쿼리",
                language="sql",
                interactive=False
            )
            
            query_button.click(
                fn=get_cypher_query,
                inputs=query_input,
                outputs=query_output
            )
        
        with gr.Tab("도움말"):
            gr.Markdown("""
            ## 📖 사용법
            
            ### 1. 설정
            - Neo4j 데이터베이스 연결 정보를 입력하세요
            - OpenAI API Key를 입력하세요
            - "챗봇 초기화" 버튼을 클릭하세요
            
            ### 2. 채팅
            - 영화에 대한 질문을 자유롭게 하세요
            - 일반적인 대화도 가능합니다
            - 예시 질문:
              - **영화 관련**: "Tom Hanks가 출연한 영화는?", "액션 영화 추천해줘"
              - **일반 대화**: "안녕하세요", "내 이름은 홍길동이야", "너는 누구야?"
            
            ### 3. 기능
            - **의도 분류**: 사용자 질문을 자동으로 분류하여 적절한 응답 제공
            - **일반 대화**: 인사, 자기소개, 일상 대화 등 자연스러운 대화
            - **영화 검색**: 영화 추천, 정보 검색, Cypher 쿼리 자동 생성
            - **자동 쿼리 생성**: 자연어를 Cypher 쿼리로 변환
            - **대화 히스토리**: 이전 대화를 기억하여 맥락 유지
            - **영화 추천**: 사용자 선호도 기반 추천
            - **쿼리 확인**: 생성된 Cypher 쿼리 확인 가능
            - **스키마 기반**: 데이터베이스 스키마를 자동으로 분석하여 쿼리 생성
            - **스키마 캐싱**: 스키마 파일이 있으면 빠르게 로드
            - **토큰 제한**: API 비용 관리를 위한 토큰 사용량 제한
            - **한국어-영어 번역**: 한국어 질문을 영어 키워드로 자동 변환
            
            ### 4. 의도 분류 시스템
            - **영화 관련 질문**: 영화 추천, 배우 정보, 장르별 영화, 평점 등
            - **일반 대화**: 인사, 자기소개, 이름 묻기, 일상 대화 등
            - 자동으로 분류되어 적절한 응답 제공
            
            ### 5. 한국어-영어 번역 기능
            - 데이터베이스의 노드와 관계는 모두 영어로 저장되어 있습니다
            - 챗봇이 한국어 질문을 자동으로 영어 키워드로 번역합니다
            - 예시:
              - "액션" → "Action"
              - "로맨스" → "Romance"  
              - "스릴러" → "Thriller"
              - "코미디" → "Comedy"
              - "Tom Hanks" → "Tom Hanks" (이름은 그대로)
            - 영화 제목은 가능하면 영어 제목을 사용하거나 영어 제목으로 검색합니다
            
            ### 6. 토큰 제한
            - 일일 최대: 50,000 토큰
            - 요청당 최대: 4,000 토큰
            - 대화 최대 길이: 20 메시지
            - 자동으로 일일 제한이 초기화됩니다
            
            ### 7. 팁
            - 구체적인 질문을 하면 더 정확한 답변을 받을 수 있습니다
            - "추천해줘"라는 키워드를 사용하면 영화 추천을 받을 수 있습니다
            - 대화가 길어지면 자동으로 요약됩니다
            - 스키마 정보를 확인하여 데이터베이스 구조를 파악할 수 있습니다
            - 스키마 파일이 있으면 초기화가 더 빠릅니다
            - 토큰 사용량을 확인하여 비용을 관리할 수 있습니다
            - 한국어로 질문해도 챗봇이 자동으로 영어 키워드로 변환합니다
            - 일반적인 대화와 영화 질문을 자유롭게 섞어서 사용할 수 있습니다
            """)
    
    return demo

# 메인 실행
if __name__ == "__main__":
    # Gradio 인터페이스 생성
    demo = create_interface()
    
    # 서버 실행
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    ) 