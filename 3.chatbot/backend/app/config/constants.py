"""
상수 정의
토큰 제한, 대화 길이 등 시스템 상수들을 정의합니다.
"""

# 토큰 제한 설정
MAX_TOKENS_PER_REQUEST = 4000  # 요청당 최대 토큰 수
MAX_TOKENS_PER_DAY = 50000     # 일일 최대 토큰 수
MAX_CONVERSATION_LENGTH = 50   # 대화 최대 길이

# 기본 스키마 파일 경로
DEFAULT_SCHEMA_FILE_PATH = "guide/movie_schema.json"

# OpenAI 모델 설정
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0
