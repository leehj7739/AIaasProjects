"""
세션 관리 유틸리티
세션 아이디 생성 및 관리 기능을 제공합니다.
"""

import uuid
import time
import hashlib
from typing import Optional

def generate_session_id(prefix: str = "session") -> str:
    """
    고유한 세션 아이디 생성
    
    Args:
        prefix: 세션 아이디 접두사 (기본값: "session")
    
    Returns:
        str: 생성된 세션 아이디 (예: session_1703123456_a1b2c3d4)
    """
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]  # UUID의 앞 8자리만 사용
    return f"{prefix}_{timestamp}_{unique_id}"

def generate_secure_session_id(prefix: str = "session", user_id: Optional[str] = None) -> str:
    """
    보안이 강화된 세션 아이디 생성
    
    Args:
        prefix: 세션 아이디 접두사 (기본값: "session")
        user_id: 사용자 ID (선택사항)
    
    Returns:
        str: 생성된 보안 세션 아이디
    """
    timestamp = int(time.time())
    random_bytes = uuid.uuid4().bytes
    
    # 사용자 ID가 있으면 포함
    if user_id:
        content = f"{timestamp}_{user_id}_{random_bytes}"
    else:
        content = f"{timestamp}_{random_bytes}"
    
    # SHA-256 해시 생성
    hash_object = hashlib.sha256(content.encode())
    hash_hex = hash_object.hexdigest()[:12]  # 12자리만 사용
    
    return f"{prefix}_{timestamp}_{hash_hex}"

def validate_session_id(session_id: str) -> bool:
    """
    세션 아이디 유효성 검사
    
    Args:
        session_id: 검사할 세션 아이디
    
    Returns:
        bool: 유효한 세션 아이디인지 여부
    """
    if not session_id:
        return False
    
    # 기본 형식 검사: prefix_timestamp_uniqueid
    parts = session_id.split('_')
    if len(parts) < 3:
        return False
    
    # 타임스탬프가 숫자인지 확인
    try:
        timestamp = int(parts[1])
        current_time = int(time.time())
        
        # 타임스탬프가 미래이거나 너무 오래된 경우 (1년 이상)
        if timestamp > current_time or timestamp < current_time - 31536000:
            return False
            
    except ValueError:
        return False
    
    return True

def extract_session_info(session_id: str) -> dict:
    """
    세션 아이디에서 정보 추출
    
    Args:
        session_id: 세션 아이디
    
    Returns:
        dict: 추출된 정보 (prefix, timestamp, unique_id)
    """
    if not validate_session_id(session_id):
        return {}
    
    parts = session_id.split('_')
    return {
        "prefix": parts[0],
        "timestamp": int(parts[1]),
        "unique_id": parts[2],
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(parts[1])))
    } 