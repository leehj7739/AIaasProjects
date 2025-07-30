"""
의도 분류 서비스
사용자의 질문이 영화 관련인지 일반 대화인지 분류합니다.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings

class IntentClassifier:
    """사용자 의도를 분류하는 클래스"""
    
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(
            model_name=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key
        )
        
        # 의도 분류 프롬프트
        self.intent_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """당신은 사용자의 의도를 분류하는 전문가입니다.
                사용자의 질문이 영화 데이터베이스와 관련된 것인지, 일반적인 대화인지 판단해주세요.
                
                영화 관련 질문의 예시:
                - 영화 추천, 영화 정보, 배우 정보, 감독 정보
                - 장르별 영화, 평점, 개봉년도, 영화 제목
                - "Tom Hanks 영화", "액션 영화 추천", "The Matrix 비슷한 영화"
                - "평점 높은 영화", "2020년 영화", "로맨스 영화"
                
                일반 대화의 예시:
                - 인사, 자기소개, 이름 묻기, 날씨, 일상 대화
                - "안녕하세요", "내 이름은 홍길동이야", "오늘 날씨 어때?"
                - "너는 누구야?", "잘 지내?", "고마워"
                
                응답 형식:
                - 영화 관련: "MOVIE"
                - 일반 대화: "GENERAL"
                - 확실하지 않으면: "GENERAL"
                
                분류만 반환하고 설명은 하지 마세요."""
            ),
            ("human", "{input}")
        ])
        
        # 의도 분류 체인
        self.intent_chain = self.intent_prompt | self.llm
    
    def classify_intent(self, user_input):
        """사용자 입력의 의도를 분류"""
        try:
            intent_response = self.intent_chain.invoke({"input": user_input})
            intent = intent_response.content.strip().upper()
            
            print(f"의도 분류: {intent} - 입력: {user_input}")
            
            return intent
        except Exception as e:
            print(f"의도 분류 실패: {e}")
            return "GENERAL"  # 기본값
    
    def is_movie_related(self, user_input):
        """영화 관련 질문인지 확인"""
        intent = self.classify_intent(user_input)
        return intent == "MOVIE"
    
    def is_general_conversation(self, user_input):
        """일반 대화인지 확인"""
        intent = self.classify_intent(user_input)
        return intent == "GENERAL" 