"""
포맷팅 유틸리티 모듈
데이터 포맷팅 및 표시 관련 유틸리티 함수들
"""

from typing import List, Dict, Any

def format_database_info(movie_count: int, actor_count: int, genre_count: int) -> str:
    """데이터베이스 정보를 포맷팅"""
    return f"""
    📊 데이터베이스 정보:
    
    🎬 영화: {movie_count:,}개
    👥 배우: {actor_count:,}개  
    🎭 장르: {genre_count:,}개
    
    총 {movie_count + actor_count + genre_count:,}개의 노드가 있습니다.
    """

def format_token_usage(daily_usage: int, remaining_tokens: int, 
                      max_daily_tokens: int, max_request_tokens: int, 
                      max_conversation_length: int) -> str:
    """토큰 사용량 정보를 포맷팅"""
    usage_percentage = (daily_usage / max_daily_tokens) * 100
    
    return f"""
    🔢 토큰 사용량:
    
    📅 일일 사용량: {daily_usage:,} / {max_daily_tokens:,} 토큰 ({usage_percentage:.1f}%)
    ⏳ 남은 토큰: {remaining_tokens:,} 토큰
    📝 요청당 최대: {max_request_tokens:,} 토큰
    💬 대화 최대 길이: {max_conversation_length} 메시지
    
    {'⚠️ 일일 한도에 근접했습니다!' if usage_percentage > 80 else '✅ 여유로운 사용량입니다.'}
    """

def extract_poster_urls(results: List[Dict]) -> List[str]:
    """검색 결과에서 포스터 URL 추출"""
    posters = []
    
    for result in results:
        if isinstance(result, dict):
            # 다양한 키 이름으로 포스터 URL 찾기
            poster_url = None
            for key in ['m.poster', 'poster', 'movie_poster']:
                if key in result and result[key]:
                    poster_url = result[key]
                    break
            
            if poster_url and poster_url not in posters:
                posters.append(poster_url)
    
    return posters[:6]  # 최대 6개 포스터만 반환

def format_search_results(results: List[Dict]) -> str:
    """검색 결과를 읽기 쉬운 형태로 포맷팅"""
    if not results:
        return "검색 결과가 없습니다."
    
    formatted_lines = []
    for i, result in enumerate(results[:10], 1):  # 최대 10개만
        if isinstance(result, dict):
            # 영화 제목
            title = result.get('m.title', result.get('title', '제목 없음'))
            
            # 평점
            rating = result.get('avg_rating', result.get('rating', ''))
            rating_text = f" (평점: {rating:.1f})" if rating else ""
            
            # 배우
            actor = result.get('a.name', result.get('actor', ''))
            actor_text = f" - {actor}" if actor else ""
            
            line = f"{i}. {title}{rating_text}{actor_text}"
            formatted_lines.append(line)
        else:
            formatted_lines.append(f"{i}. {result}")
    
    return "\n".join(formatted_lines)

def format_cypher_query(query: str) -> str:
    """Cypher 쿼리를 읽기 쉽게 포맷팅"""
    if not query:
        return "쿼리가 없습니다."
    
    # 기본 포맷팅
    formatted = query.strip()
    
    # 키워드별 줄바꿈 추가
    keywords = ['MATCH', 'WHERE', 'RETURN', 'ORDER BY', 'LIMIT', 'WITH']
    for keyword in keywords:
        formatted = formatted.replace(f' {keyword} ', f'\n{keyword} ')
    
    return formatted

def format_error_message(error: str) -> str:
    """오류 메시지를 사용자 친화적으로 포맷팅"""
    if "connection" in error.lower():
        return "❌ 데이터베이스 연결에 실패했습니다. 설정을 확인해주세요."
    elif "authentication" in error.lower():
        return "❌ 인증에 실패했습니다. 사용자명과 비밀번호를 확인해주세요."
    elif "timeout" in error.lower():
        return "⏰ 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    elif "syntax" in error.lower():
        return "🔧 쿼리 문법에 오류가 있습니다."
    else:
        return f"❌ 오류가 발생했습니다: {error}"

def format_success_message(message: str) -> str:
    """성공 메시지를 포맷팅"""
    return f"✅ {message}"

def format_warning_message(message: str) -> str:
    """경고 메시지를 포맷팅"""
    return f"⚠️ {message}"

def format_info_message(message: str) -> str:
    """정보 메시지를 포맷팅"""
    return f"ℹ️ {message}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """텍스트를 지정된 길이로 자르기"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def format_list(items: List[Any], max_items: int = 10) -> str:
    """리스트를 포맷팅"""
    if not items:
        return "항목이 없습니다."
    
    formatted_items = []
    for i, item in enumerate(items[:max_items], 1):
        formatted_items.append(f"{i}. {item}")
    
    if len(items) > max_items:
        formatted_items.append(f"... 외 {len(items) - max_items}개")
    
    return "\n".join(formatted_items) 