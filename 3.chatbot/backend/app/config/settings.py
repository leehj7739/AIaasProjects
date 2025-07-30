"""
환경변수 및 설정 관리
dotenv를 사용하여 환경변수를 로드하고 설정을 관리합니다.
"""

import os
from dotenv import load_dotenv
from .constants import *

# 환경변수 로드
load_dotenv()

class Settings:
    """애플리케이션 설정 클래스"""
    
    def __init__(self):
        # Neo4j 설정
        self.neo4j_uri = os.getenv("NEO4J_URI", "")
        self.neo4j_user = os.getenv("NEO4J_USER", "")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        
        # OpenAI 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", DEFAULT_TEMPERATURE))
        
        # 스키마 설정
        self.schema_file_path = os.getenv("SCHEMA_FILE_PATH", DEFAULT_SCHEMA_FILE_PATH)
        
        # 토큰 제한 설정
        self.max_tokens_per_request = int(os.getenv("MAX_TOKENS_PER_REQUEST", MAX_TOKENS_PER_REQUEST))
        self.max_tokens_per_day = int(os.getenv("MAX_TOKENS_PER_DAY", MAX_TOKENS_PER_DAY))
        self.max_conversation_length = int(os.getenv("MAX_CONVERSATION_LENGTH", MAX_CONVERSATION_LENGTH))
        
    def validate(self):
        """설정 유효성 검사"""
        errors = []
        
        if not self.openai_api_key:
            errors.append("OpenAI API Key가 설정되지 않았습니다.")
        
        if not self.neo4j_uri:
            errors.append("Neo4j URI가 설정되지 않았습니다.")
        
        if not self.neo4j_user:
            errors.append("Neo4j 사용자명이 설정되지 않았습니다.")
        
        if not self.neo4j_password:
            errors.append("Neo4j 비밀번호가 설정되지 않았습니다.")
        
        return errors
    
    def get_neo4j_config(self):
        """Neo4j 설정 반환"""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password
        }
    
    def get_openai_config(self):
        """OpenAI 설정 반환"""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.openai_temperature
        }

# 전역 설정 인스턴스
settings = Settings() 