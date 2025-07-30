"""
Cypher 쿼리 생성 서비스
자연어를 Neo4j Cypher 쿼리로 변환합니다.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings
from utils.data_utils import generate_examples_from_schema

class CypherGenerator:
    """Cypher 쿼리를 생성하는 클래스"""
    
    def __init__(self, llm=None, schema=None):
        self.llm = llm or ChatOpenAI(
            model_name=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key
        )
        self.schema = schema
        self.examples = generate_examples_from_schema(schema) if schema else []
        
        # Cypher 쿼리 생성 프롬프트
        self.cypher_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"""당신은 Neo4j Cypher 쿼리 생성 전문가입니다.
                사용자의 자연어 질문을 정확한 Cypher 쿼리로 변환해주세요.
                
                데이터베이스 스키마:
                {self._format_schema_for_prompt()}
                
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
                   - 복합적인 경우 위의 규칙을 적절히 섞어서 사용하세요
                
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
    
    def _format_schema_for_prompt(self):
        """프롬프트용 스키마 포맷팅"""
        if not self.schema:
            return "스키마 정보가 없습니다."
        
        result = []

        # 노드 프로퍼티 출력
        result.append("Node properties:")
        for label, properties in self.schema["nodes"].items():
            props = ", ".join(f"{k}: {v}" for k, v in properties.items())
            result.append(f"{label} {{{{{props}}}}}")  # 이중 중괄호로 이스케이프

        # 관계 프로퍼티 출력
        result.append("Relationship properties:")
        for rel_type, properties in self.schema["relationships"].items():
            props = ", ".join(f"{k}: {v}" for k, v in properties.items())
            result.append(f"{rel_type} {{{{{props}}}}}")  # 이중 중괄호로 이스케이프

        # 관계 출력
        result.append("The relationships:")
        for relation in self.schema["relations"]:
            result.append(relation)

        return "\n".join(result)
    
    def update_schema(self, schema):
        """스키마 업데이트"""
        self.schema = schema
        self.examples = generate_examples_from_schema(schema)
        
        # 프롬프트 업데이트
        self.cypher_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"""당신은 Neo4j Cypher 쿼리 생성 전문가입니다.
                사용자의 자연어 질문을 정확한 Cypher 쿼리로 변환해주세요.
                
                데이터베이스 스키마:
                {self._format_schema_for_prompt()}
                
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
                   - 복합적인 경우 위의 규칙을 적절히 섞어서 사용하세요
                
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
        
        # 체인 업데이트
        self.cypher_chain = self.cypher_prompt | self.llm
    
    def generate_cypher_query(self, user_input):
        """사용자 입력으로부터 Cypher 쿼리 생성"""
        try:
            cypher_response = self.cypher_chain.invoke({"input": user_input})
            cypher_query = cypher_response.content.strip()
            
            print(f"생성된 Cypher 쿼리: {cypher_query}")
            
            return cypher_query
        except Exception as e:
            print(f"Cypher 쿼리 생성 실패: {e}")
            return ""
    
    def validate_cypher_query(self, cypher_query):
        """Cypher 쿼리 유효성 검사"""
        if not cypher_query:
            return False, "쿼리가 비어있습니다."
        
        # 기본적인 Cypher 키워드 확인
        required_keywords = ["MATCH", "RETURN"]
        for keyword in required_keywords:
            if keyword not in cypher_query.upper():
                return False, f"필수 키워드 '{keyword}'가 없습니다."
        
        return True, "유효한 쿼리입니다." 