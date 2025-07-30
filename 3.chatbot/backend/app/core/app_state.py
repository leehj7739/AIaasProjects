"""
애플리케이션 전역 상태 관리
DB 서비스와 스키마 매니저를 전역적으로 관리합니다.
"""

from services.database_service import DatabaseService
from core.schema_manager import SchemaManager

# 전역 변수로 DB 서비스와 스키마 매니저 저장
db_service = None
schema_manager = None

def initialize_app_state():
    """애플리케이션 상태 초기화"""
    global db_service, schema_manager
    
    print("🚀 애플리케이션 상태 초기화 중...")
    
    try:
        from config.settings import settings
        
        # 1. 설정 유효성 검사
        errors = settings.validate()
        if errors:
            print("❌ 설정 오류:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ 설정 유효성 검사 통과")
        
        # 2. 데이터베이스 연결 초기화
        print("🔗 데이터베이스 연결 초기화 중...")
        db_service = DatabaseService()
        
        # 3. 데이터베이스 연결 테스트
        connection_test = db_service.test_connection()
        if connection_test["status"] == "success":
            print("✅ 데이터베이스 연결 성공")
        else:
            print(f"❌ 데이터베이스 연결 실패: {connection_test['message']}")
            return False
        
        # 4. 스키마 매니저 초기화
        print("📋 스키마 매니저 초기화 중...")
        schema_manager = SchemaManager(
            driver=db_service.driver,
            schema_file_path=settings.schema_file_path
        )
        
        # 5. 스키마 로드 또는 추출
        schema = schema_manager.get_or_load_schema()
        if schema:
            print("✅ 스키마 로드 완료")
        else:
            print("❌ 스키마 로드 실패")
            return False
        
        # 6. 데이터베이스 정보 출력
        db_info = db_service.get_database_info()
        print(f"📊 데이터베이스 정보:")
        print(f"  - 영화: {db_info['movie_count']}개")
        print(f"  - 배우: {db_info['actor_count']}명")
        print(f"  - 장르: {db_info['genre_count']}개")
        
        print("🎉 애플리케이션 상태 초기화 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 애플리케이션 상태 초기화 실패: {e}")
        return False

def cleanup_app_state():
    """애플리케이션 상태 정리"""
    global db_service
    
    print("🛑 애플리케이션 상태 정리 중...")
    
    if db_service:
        db_service.close()
        print("✅ 데이터베이스 연결 종료")
    
    print("👋 애플리케이션 상태 정리 완료")

def get_db_service():
    """DB 서비스 반환"""
    return db_service

def get_schema_manager():
    """스키마 매니저 반환"""
    return schema_manager

def is_initialized():
    """애플리케이션이 초기화되었는지 확인"""
    return db_service is not None and schema_manager is not None 