"""
데이터 유틸리티 모듈
데이터 타입 추론 및 스키마 관련 유틸리티 함수들
"""

import re
from typing import Any, Dict, List

def get_node_datatype(value: Any) -> str:
    """값의 데이터 타입을 추론하여 Neo4j 스키마 형식으로 반환"""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        # URL 패턴 확인
        if re.match(r'^https?://', value):
            return "url"
        # 날짜 패턴 확인
        elif re.match(r'^\d{4}-\d{2}-\d{2}', value):
            return "date"
        # 이메일 패턴 확인
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            return "email"
        else:
            return "string"
    elif isinstance(value, list):
        return "list"
    elif isinstance(value, dict):
        return "object"
    else:
        return "string"

def generate_examples_from_schema(schema: Dict) -> List[str]:
    """스키마로부터 예시 쿼리들을 생성"""
    examples = []
    
    if not schema:
        return examples
    
    # 기본 예시들
    examples.extend([
        "사용자 질문: Tom Hanks가 출연한 영화는?",
        "Cypher 쿼리: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE a.name = 'Tom Hanks' RETURN m.title, m.poster",
        "",
        "사용자 질문: 액션 영화 추천해줘",
        "Cypher 쿼리: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE g.name = 'Action' RETURN m.title, m.poster LIMIT 10",
        "",
        "사용자 질문: The Matrix와 비슷한 영화는?",
        "Cypher 쿼리: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre) WHERE g.name = 'Action' RETURN m.title, m.poster LIMIT 10",
        "",
        "사용자 질문: 로맨스 영화 중에서 평점이 높은 것들은?",
        "Cypher 쿼리: MATCH (m:Movie)-[:IN_GENRE]->(g:Genre), (u:User)-[r:RATED]->(m) WHERE g.name = 'Romance' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC",
        "",
        "사용자 질문: Leonardo DiCaprio의 최고 작품은?",
        "Cypher 쿼리: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)<-[r:RATED]-(u:User) WHERE a.name = 'Leonardo DiCaprio' RETURN m.title, m.poster, AVG(r.rating) as avg_rating ORDER BY avg_rating DESC LIMIT 5"
    ])
    
    return examples

def extract_movie_info(record: Dict) -> Dict:
    """Neo4j 레코드에서 영화 정보 추출"""
    movie_info = {}
    
    # 영화 제목
    if 'm.title' in record:
        movie_info['title'] = record['m.title']
    elif 'title' in record:
        movie_info['title'] = record['title']
    
    # 포스터 URL
    if 'm.poster' in record:
        movie_info['poster'] = record['m.poster']
    elif 'poster' in record:
        movie_info['poster'] = record['poster']
    
    # 평점
    if 'avg_rating' in record:
        movie_info['rating'] = round(record['avg_rating'], 1)
    elif 'rating' in record:
        movie_info['rating'] = record['rating']
    
    # 배우 이름
    if 'a.name' in record:
        movie_info['actor'] = record['a.name']
    elif 'actor' in record:
        movie_info['actor'] = record['actor']
    
    # 장르
    if 'g.name' in record:
        movie_info['genre'] = record['g.name']
    elif 'genre' in record:
        movie_info['genre'] = record['genre']
    
    return movie_info

def format_cypher_result(results: List[Dict]) -> List[Dict]:
    """Cypher 쿼리 결과를 포맷팅"""
    formatted_results = []
    
    for result in results:
        formatted_result = {}
        
        for key, value in result.items():
            # Neo4j 노드나 관계 객체 처리
            if hasattr(value, 'get'):
                if 'name' in value:
                    formatted_result[key] = value['name']
                elif 'title' in value:
                    formatted_result[key] = value['title']
                else:
                    formatted_result[key] = str(value)
            else:
                formatted_result[key] = value
        
        formatted_results.append(formatted_result)
    
    return formatted_results

def validate_cypher_query(query: str) -> bool:
    """Cypher 쿼리 기본 유효성 검사"""
    if not query or not query.strip():
        return False
    
    # 기본 키워드 확인
    required_keywords = ['MATCH', 'RETURN']
    query_upper = query.upper()
    
    for keyword in required_keywords:
        if keyword not in query_upper:
            return False
    
    return True

def sanitize_input(text: str) -> str:
    """사용자 입력 정제"""
    if not text:
        return ""
    
    # 특수 문자 제거 (기본적인 것만)
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # 공백 정리
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.strip() 