"""
데이터베이스 서비스 모듈
Neo4j 데이터베이스 연결 및 쿼리 실행을 담당합니다.
"""

from neo4j import GraphDatabase, basic_auth
from config.settings import settings

class DatabaseService:
    """Neo4j 데이터베이스 서비스 클래스"""
    
    def __init__(self, uri=None, user=None, password=None):
        """데이터베이스 서비스 초기화"""
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.driver = None
        
        # 드라이버 초기화
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Neo4j 드라이버 초기화"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=basic_auth(self.user, self.password)
            )
            print(f"✅ Neo4j 드라이버 초기화 완료: {self.uri}")
        except Exception as e:
            print(f"❌ Neo4j 드라이버 초기화 실패: {e}")
            self.driver = None
    
    def test_connection(self):
        """데이터베이스 연결 테스트"""
        try:
            if not self.driver:
                return {"status": "error", "message": "드라이버가 초기화되지 않았습니다."}
            
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                
                if record and record["test"] == 1:
                    return {"status": "success", "message": "✅ Neo4j 연결 성공!"}
                else:
                    return {"status": "error", "message": "❌ 연결 테스트 실패"}
                    
        except Exception as e:
            return {"status": "error", "message": f"❌ 연결 오류: {str(e)}"}
    
    def execute_query(self, cypher_query):
        """Cypher 쿼리 실행"""
        try:
            if not self.driver:
                raise Exception("드라이버가 초기화되지 않았습니다.")
            
            with self.driver.session() as session:
                result = session.run(cypher_query)
                records = list(result)
                
                # 결과를 딕셔너리 리스트로 변환
                results = []
                for record in records:
                    record_dict = {}
                    for key, value in record.items():
                        # Neo4j 노드나 관계 객체를 딕셔너리로 변환
                        if hasattr(value, 'get'):
                            record_dict[key] = value.get('name', value.get('title', str(value)))
                        else:
                            record_dict[key] = value
                    results.append(record_dict)
                
                print(f"✅ 쿼리 실행 완료: {len(results)}개 결과")
                return results
                
        except Exception as e:
            print(f"❌ 쿼리 실행 실패: {e}")
            raise e
    
    def test_cypher_query(self, cypher_query):
        """Cypher 쿼리 테스트"""
        try:
            results = self.execute_query(cypher_query)
            return {
                "status": "success",
                "results": results,
                "count": len(results),
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "results": [],
                "count": 0,
                "error": str(e)
            }
    
    def get_database_info(self):
        """데이터베이스 정보 조회"""
        try:
            if not self.driver:
                return {"movie_count": 0, "actor_count": 0, "genre_count": 0}
            
            with self.driver.session() as session:
                # 영화 수 조회
                movie_result = session.run("MATCH (m:Movie) RETURN count(m) as count")
                movie_count = movie_result.single()["count"]
                
                # 배우 수 조회
                actor_result = session.run("MATCH (a:Actor) RETURN count(a) as count")
                actor_count = actor_result.single()["count"]
                
                # 장르 수 조회
                genre_result = session.run("MATCH (g:Genre) RETURN count(g) as count")
                genre_count = genre_result.single()["count"]
                
                return {
                    "movie_count": movie_count,
                    "actor_count": actor_count,
                    "genre_count": genre_count
                }
                
        except Exception as e:
            print(f"❌ 데이터베이스 정보 조회 실패: {e}")
            return {"movie_count": 0, "actor_count": 0, "genre_count": 0}
    
    def get_sample_data(self):
        """샘플 데이터 조회"""
        try:
            if not self.driver:
                return []
            
            with self.driver.session() as session:
                # 샘플 영화 조회
                result = session.run("""
                    MATCH (m:Movie)
                    RETURN m.title as title, m.poster as poster
                    LIMIT 5
                """)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            print(f"❌ 샘플 데이터 조회 실패: {e}")
            return []
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j 연결 종료") 