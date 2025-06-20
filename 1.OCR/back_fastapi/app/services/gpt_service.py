from openai import OpenAI
from typing import Optional
import asyncio
import time

from app.models.response import GPTResponse
from app.config.settings import settings
from app.core.exceptions import GPTException

class GPTService:
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        if not settings.OPENAI_API_KEY:
            raise GPTException("OpenAI API 키가 설정되지 않았습니다.")
        
        # 새로운 OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def analyze_text(self, text: str, prompt: str = "") -> GPTResponse:
        """텍스트 분석 및 GPT 응답"""
        try:
            start_time = time.time()
            
            # 프롬프트 구성
            full_prompt = f"{prompt}\n\n텍스트: {text}"
            
            # 새로운 GPT API 호출 방식
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # 응답 추출
            gpt_response = response.choices[0].message.content
            usage = response.usage
            
            return GPTResponse(
                original_text=text,
                prompt=prompt,
                gpt_response=gpt_response,
                gpt_model=self.model,
                tokens_used=usage.total_tokens if usage else 0,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            raise GPTException(f"GPT 분석 실패: {str(e)}")
    
    async def extract_book_title(self, text: str) -> GPTResponse:
        """책 표지에서 제목 추출"""
        try:
            start_time = time.time()
            
            # 책 제목 추론 전문가 역할 설정 (대폭 보강된 프롬프트)
            system_prompt = """당신은 책 제목 추출 전문가입니다. 
OCR로 추출된 텍스트에서 가장 가능성이 높은 책 제목을 정확하게 추출하는 것이 당신의 임무입니다.

📚 책 제목 추출 규칙:
1. **핵심 키워드 우선**: 가장 의미 있고 독립적인 단어나 구를 찾으세요
2. **길이 고려**: 책 제목은 보통 2-8단어 정도입니다
3. **언어 우선순위**: 한글 > 영어 > 기타 순서로 우선하세요
4. **노이즈 제거**: 특수문자, 숫자, 불필요한 기호는 제거하세요
5. **문맥 분석**: 전체 텍스트를 보고 가장 책 제목다운 조합을 찾으세요
6. **일반적인 책 제목 패턴**: 
   - "~의 ~" (경험의 멸종, 마음의 기술)
   - "~론" (자유론, 민주주의론)
   - "~하다" (싯다르타, 위버멘쉬)
   - 단일 단어 (넥서스, 자유)

🔍 추출 과정:
1. 텍스트에서 의미 있는 단어들을 식별
2. 책 제목 패턴에 맞는 조합을 찾기
3. 가장 자연스럽고 완성도 높은 제목 선택
4. 확신이 없으면 "추정:" 표기

❌ 피해야 할 것들:
- 저자명, 출판사명
- 부제목이나 설명문
- 너무 긴 문장
- 의미 없는 조합"""
            
            user_prompt = f"""다음은 책 표지에서 OCR로 추출된 텍스트입니다.
위의 규칙을 따라 가장 책 제목일 확률이 높은 텍스트를 정확하게 추출해주세요.

📖 추출된 텍스트: {text}

💡 힌트: 
- 노이즈가 많아도 핵심 키워드를 찾아보세요
- 한글과 영어가 섞여있으면 한글을 우선하세요
- 책 제목은 보통 간결하고 의미가 명확합니다
- 전체적인 맥락을 고려하여 추론하세요"""
            
            # 새로운 GPT API 호출 방식
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.1  # 매우 낮은 temperature로 일관성 확보
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # 응답 추출
            gpt_response = response.choices[0].message.content
            usage = response.usage
            
            # 응답 후처리: "추정:" 부분 제거하고 실제 제목만 추출
            cleaned_response = self._clean_book_title_response(gpt_response)
            
            return GPTResponse(
                original_text=text,
                prompt="책 제목 추출",
                gpt_response=cleaned_response,
                gpt_model=self.model,
                tokens_used=usage.total_tokens if usage else 0,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            raise GPTException(f"책 제목 추출 실패: {str(e)}")
    
    async def summarize_text(self, text: str) -> GPTResponse:
        """텍스트 요약"""
        prompt = "다음 텍스트를 간결하고 명확하게 요약해주세요:"
        return await self.analyze_text(text, prompt)
    
    async def translate_text(self, text: str, target_language: str = "한국어") -> GPTResponse:
        """텍스트 번역"""
        prompt = f"다음 텍스트를 {target_language}로 번역해주세요:"
        return await self.analyze_text(text, prompt)
    
    async def extract_keywords(self, text: str) -> GPTResponse:
        """키워드 추출"""
        prompt = "다음 텍스트에서 중요한 키워드들을 추출해주세요 (쉼표로 구분):"
        return await self.analyze_text(text, prompt)
    
    async def answer_question(self, text: str, question: str) -> GPTResponse:
        """텍스트 기반 질문 답변"""
        prompt = f"다음 텍스트를 바탕으로 질문에 답변해주세요.\n\n질문: {question}"
        return await self.analyze_text(text, prompt)
    
    def _clean_book_title_response(self, response: str) -> str:
        """책 제목 응답에서 불필요한 부분을 제거하고 실제 제목만 추출"""
        if not response:
            return ""
        
        # "추정:" 제거
        if "추정:" in response:
            response = response.replace("추정:", "").strip()
        
        # "제목:" 제거
        if "제목:" in response:
            response = response.replace("제목:", "").strip()
        
        # 따옴표 제거
        response = response.strip('"\'')
        
        # 줄바꿈 제거하고 공백 정리
        response = " ".join(response.split())
        
        return response
    
    async def batch_analyze(self, texts: list, prompt: str = "") -> list[GPTResponse]:
        """여러 텍스트 일괄 분석"""
        try:
            tasks = [self.analyze_text(text, prompt) for text in texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외 처리
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        GPTResponse(
                            original_text=texts[i],
                            prompt=prompt,
                            gpt_response=f"오류 발생: {str(result)}",
                            gpt_model=self.model,
                            tokens_used=0,
                            response_time_ms=0
                        )
                    )
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            raise GPTException(f"배치 분석 실패: {str(e)}") 