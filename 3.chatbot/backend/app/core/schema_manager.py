"""
스키마 관리 모듈
Neo4j 데이터베이스 스키마를 로드, 캐싱, 포맷팅합니다.
"""

import os
import json
from neo4j import GraphDatabase, basic_auth
from utils.data_utils import get_node_datatype
from config import settings

class SchemaManager:
    """Neo4j 스키마를 관리하는 클래스"""
    
    def __init__(self, driver=None, schema_file_path=settings.schema_file_path):
        self.driver = driver
        self.schema_file_path = schema_file_path
        self.schema = None
        self.formatted_schema = ""
        self.examples = []
    
    def set_driver(self, driver):
        """Neo4j 드라이버 설정"""
        self.driver = driver
    
    def load_schema_from_file(self):
        """스키마 파일에서 로드하는 함수"""
        try:
            if os.path.exists(self.schema_file_path):
                with open(self.schema_file_path, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    print(f"✅ 스키마 파일에서 로드됨: {self.schema_file_path}")
                    return schema_data.get("schema", None)
            else:
                print(f"⚠️ 스키마 파일이 없습니다: {self.schema_file_path}")
                return None
        except Exception as e:
            print(f"❌ 스키마 파일 로드 실패: {e}")
            return None
    
    def extract_schema_from_database(self):
        """Graph DB의 정보를 받아 노드 및 관계의 프로퍼티를 추출하고 스키마 딕셔너리를 반환하는 함수"""
        if not self.driver:
            raise ValueError("Neo4j 드라이버가 설정되지 않았습니다.")
        
        try:
            with self.driver.session() as session:
                # 노드 프로퍼티 및 타입 추출
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

                # 관계 프로퍼티 및 타입 추출
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

                # 관계 유형 및 방향 추출
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
    
    def save_schema_to_file(self, schema):
        """스키마를 파일로 저장"""
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(self.schema_file_path), exist_ok=True)
            
            # 스키마를 파일로 저장
            with open(self.schema_file_path, 'w', encoding='utf-8') as f:
                json.dump({"schema": schema}, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 스키마를 파일로 저장했습니다: {self.schema_file_path}")
            return True
        except Exception as e:
            print(f"❌ 스키마 파일 저장 실패: {e}")
            return False
    
    def get_or_load_schema(self):
        """스키마를 파일에서 로드하거나 데이터베이스에서 추출"""
        try:
            # 먼저 파일에서 로드 시도
            schema = self.load_schema_from_file()
            if schema:
                print(f"✅ 스키마를 파일에서 로드했습니다: {self.schema_file_path}")
                self.schema = schema
                return schema
        except Exception as e:
            print(f"⚠️ 스키마 파일 로드 실패: {e}")
        
        try:
            # 파일이 없거나 로드 실패시 데이터베이스에서 추출
            print("🔄 데이터베이스에서 스키마 추출 중...")
            schema = self.extract_schema_from_database()
            
            if schema:
                # 스키마를 파일로 저장
                self.save_schema_to_file(schema)
                self.schema = schema
                print(f"✅ 스키마를 데이터베이스에서 추출하여 저장했습니다: {self.schema_file_path}")
                return schema
            else:
                raise ValueError("스키마 추출에 실패했습니다.")
                
        except Exception as e:
            print(f"❌ 스키마 추출 실패: {e}")
            # 기본 스키마 반환
            print("🔄 기본 스키마 사용")
            self.schema = self._get_default_schema()
            return self.schema
    
    def _get_default_schema(self):
        """기본 스키마 반환"""
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
    
    def format_schema(self):
        """스키마 딕셔너리를 LLM에 제공하기 위해 원하는 형태로 formatting 하는 함수"""
        if not self.schema:
            return ""
        
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

        self.formatted_schema = "\n".join(result)
        return self.formatted_schema
    
    def get_schema_info(self):
        """스키마 정보 반환"""
        return {
            "schema": self.schema,
            "formatted_schema": self.formatted_schema,
            "examples": self.examples
        } 