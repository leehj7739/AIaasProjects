"""
응답 생성 서비스
사용자 질문에 대한 적절한 응답을 생성합니다.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings

class ResponseGenerator:
    """응답을 생성하는 클래스"""
    
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(
            model_name=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key
        )
        
        # 영화 응답 생성 프롬프트
        self.movie_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """당신은 영화 추천 챗봇입니다.
                사용자의 질문에 대해 친근하고 도움이 되는 답변을 제공해주세요.
                
                답변 규칙:
                1. 한국어로 답변하세요
                2. 친근하고 자연스러운 톤을 사용하세요
                3. 영화 정보가 있으면 포스터 이미지도 언급하세요
                4. 평점 정보가 있으면 평점도 포함하세요
                5. 영화가 없으면 다른 추천을 제안하세요
                6. 이모지를 적절히 사용하여 친근감을 주세요
                7. 대화 히스토리를 참고하여 맥락을 유지하세요
                8. 에러가 발생한경우 에러 메시지를 보내지말고 서비스 이용이 어렵다고 안내하세요
                
                예시 답변:
                - "🎬 'The Matrix'와 비슷한 영화를 찾아드렸어요! 'Inception'이 추천드립니다. 크리스토퍼 놀란 감독의 작품으로, 꿈과 현실의 경계를 다룬 SF 액션 영화예요."
                - "⭐ Tom Hanks의 최고 평점 영화는 'Forrest Gump'입니다. 평점 9.2점으로 많은 사랑을 받고 있어요!"
                - "😊 로맨스 영화를 찾고 계시는군요! 'The Notebook'을 추천드려요. 평점 8.1점의 감동적인 로맨스 영화입니다."
                """
            ),
            ("human", "사용자 질문: {question}\n\n검색 결과: {results}\n\n대화 히스토리: {history}")
        ])
        
        # 일반 대화 응답 생성 프롬프트
        self.general_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
                사용자와 자연스럽고 친근한 대화를 나누어주세요.
                
                대화 규칙:
                1. 한국어로 답변하세요
                2. 친근하고 자연스러운 톤을 사용하세요
                3. 이모지를 적절히 사용하여 친근감을 주세요
                4. 사용자의 이름을 기억하고 사용하세요
                5. 대화 히스토리를 참고하여 맥락을 유지하세요
                6. 영화 추천 챗봇이라는 것을 언급할 수 있습니다
                8. 에러가 발생한경우 에러 메시지를 보내지말고 서비스 이용이 어렵다고 안내하세요
                
                예시 답변:
                - "안녕하세요! 😊 영화 추천 챗봇입니다. 무엇을 도와드릴까요?"
                - "홍길동님, 반갑습니다! 🎬 영화에 대해 궁금한 것이 있으시면 언제든 물어보세요!"
                - "고마워요! 😊 영화 추천이나 정보가 필요하시면 언제든 말씀해주세요."
                """
            ),
            ("human", "사용자 질문: {question}\n\n대화 히스토리: {history}")
        ])
        
        # 대화 요약 프롬프트
        self.summary_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """대화 히스토리를 간결하게 요약해주세요.
                중요한 정보와 맥락을 유지하면서 핵심만 추출하세요.
                
                요약 규칙:
                1. 사용자의 이름과 선호도 정보 유지
                2. 주요 영화 추천이나 질문 내용 포함
                3. 간결하고 명확하게 작성
                4. 이모지 사용으로 친근감 유지
                
                예시:
                "홍길동님이 Tom Hanks 영화와 액션 영화에 관심을 보이셨고, 'The Matrix'와 비슷한 영화를 추천받으셨습니다."
                """
            ),
            ("human", "대화 히스토리: {history}")
        ])
        
        # 체인 생성
        self.movie_chain = self.movie_prompt | self.llm
        self.general_chain = self.general_prompt | self.llm
        self.summary_chain = self.summary_prompt | self.llm
    
    def generate_movie_response(self, question, results, history=None):
        """영화 관련 질문에 대한 응답 생성"""
        try:
            # 대화 히스토리 포맷팅
            history_text = self._format_history(history) if history else ""
            
            # 검색 결과 포맷팅
            results_text = self._format_results(results)
            
            response = self.movie_chain.invoke({
                "question": question,
                "results": results_text,
                "history": history_text
            })
            
            return response.content.strip()
        except Exception as e:
            print(f"영화 응답 생성 실패: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    def generate_general_response(self, question, history=None):
        """일반 대화에 대한 응답 생성"""
        try:
            # 대화 히스토리 포맷팅
            history_text = self._format_history(history) if history else ""
            
            response = self.general_chain.invoke({
                "question": question,
                "history": history_text
            })
            
            return response.content.strip()
        except Exception as e:
            print(f"일반 응답 생성 실패: {e}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    def summarize_conversation(self, history):
        """대화 히스토리 요약"""
        try:
            history_text = self._format_history(history)
            
            summary = self.summary_chain.invoke({
                "history": history_text
            })
            
            return summary.content.strip()
        except Exception as e:
            print(f"대화 요약 실패: {e}")
            return "대화 요약을 생성할 수 없습니다."
    
    def _format_history(self, history):
        """대화 히스토리 포맷팅"""
        if not history:
            return ""
        
        formatted = []
        for i, message in enumerate(history):
            role = "user" if i % 2 == 0 else "assistant"
            content = message.content if hasattr(message, 'content') else str(message)
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _format_results(self, results):
        """검색 결과 포맷팅"""
        if not results:
            return "검색 결과가 없습니다."
        
        formatted = []
        for i, result in enumerate(results[:10], 1):  # 최대 10개만
            if isinstance(result, dict):
                title = result.get('m.title', result.get('title', '제목 없음'))
                poster = result.get('m.poster', result.get('poster', ''))
                rating = result.get('avg_rating', result.get('rating', ''))
                
                line = f"{i}. {title}"
                if rating:
                    line += f" (평점: {rating:.1f})"
                if poster:
                    line += f" [포스터: {poster}]"
                
                formatted.append(line)
            else:
                formatted.append(f"{i}. {result}")
        
        return "\n".join(formatted) if formatted else "검색 결과가 없습니다." 