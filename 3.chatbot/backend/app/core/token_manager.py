"""
토큰 관리 모듈
OpenAI API 토큰 사용량을 추적하고 제한을 관리합니다.
"""

import tiktoken
from datetime import datetime
from config import settings

class TokenManager:
    """토큰 사용량을 관리하는 클래스"""
    
    def __init__(self):
        self.daily_tokens = 0
        self.last_reset_date = datetime.now().date()
        self.encoding = tiktoken.encoding_for_model(settings.openai_model)
    
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
        
        return self.daily_tokens < settings.max_tokens_per_day
    
    def add_tokens(self, token_count):
        """토큰 사용량 추가"""
        self.daily_tokens += token_count
    
    def get_daily_usage(self):
        """일일 토큰 사용량 반환"""
        return self.daily_tokens
    
    def get_remaining_tokens(self):
        """남은 토큰 수 반환"""
        return max(0, settings.max_tokens_per_day - self.daily_tokens)
    
    def check_request_limit(self, text):
        """요청당 토큰 제한 확인"""
        token_count = self.count_tokens(text)
        return token_count <= settings.max_tokens_per_request, token_count
    
    def check_conversation_limit(self, conversation_length):
        """대화 길이 제한 확인"""
        return conversation_length < settings.max_conversation_length
    
    def reset_daily_usage(self):
        """일일 사용량 초기화"""
        self.daily_tokens = 0
        self.last_reset_date = datetime.now().date()
    
    def get_usage_stats(self):
        """사용량 통계 반환"""
        return {
            "daily_usage": self.daily_tokens,
            "remaining_tokens": self.get_remaining_tokens(),
            "max_daily_tokens": settings.max_tokens_per_day,
            "max_request_tokens": settings.max_tokens_per_request,
            "max_conversation_length": settings.max_conversation_length,
            "last_reset_date": self.last_reset_date.isoformat()
        } 