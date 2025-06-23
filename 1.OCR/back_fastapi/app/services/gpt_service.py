from openai import OpenAI
from typing import Optional
import asyncio
import time
import re

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
        
        # 특수문자 제거 (한글, 영어, 숫자, 공백만 허용)
        # 한글, 영어, 숫자, 공백만 남기고 모든 특수문자 제거
        response = re.sub(r'[^\w\s가-힣]', '', response)
        
        # 연속된 공백을 하나로 정리
        response = re.sub(r'\s+', ' ', response).strip()
        
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
    
    async def extract_book_title_with_boxes(self, text_with_boxes: str) -> GPTResponse:
        """바운딩 박스 정보를 포함한 책 제목 추출"""
        try:
            start_time = time.time()
            
            # 바운딩 박스 정보를 활용한 책 제목 추출 프롬프트
            system_prompt = """당신은 책 제목 추출 전문가입니다. 
OCR로 추출된 텍스트와 바운딩 박스 위치 정보를 활용하여 가장 가능성이 높은 책 제목을 정확하게 추출하세요.

📝 **1단계: 텍스트 보정**
먼저 각 텍스트를 정확하게 보정하세요:
- OCR 오타 수정 (예: '쇼편하우어' → '쇼펜하우어', '마혼' → '마흔')
- 불필요한 공백 제거
- 특수문자 정리 (불필요한 기호 제거)
- 한글/영어 혼용 텍스트 정리
- 숫자와 문자의 혼동 수정 (예: '0' → 'O', '1' → 'l')

📚 **2단계: 책 제목 추출 규칙 (위치 정보 활용)**
1. **위치 우선순위**: 
   - 상단 중앙에 위치한 텍스트가 책 제목일 가능성이 높음
   - 이미지의 1/3 상단 영역에 있는 텍스트 우선 고려
2. **크기와 신뢰도**: 
   - 큰 폰트 크기(바운딩 박스가 큰) 텍스트 우선
   - 높은 신뢰도 텍스트 우선
3. **배치 패턴**:
   - 중앙 정렬된 텍스트가 제목일 가능성 높음
   - 여러 줄로 구성된 제목도 고려
4. **언어 우선순위**: 한글 > 영어 > 기타
5. **길이 고려**: 책 제목은 보통 2-8단어 정도

🔍 **분석 과정**:
1. 각 텍스트를 정확하게 보정
2. 위치 정보를 바탕으로 상단 영역 텍스트 식별
3. 신뢰도와 바운딩 박스 크기 고려
4. 가장 책 제목다운 조합 선택
5. 확신이 없으면 "추정:" 표기

❌ **피해야 할 것들**:
- 하단에 위치한 저자명, 출판사명
- 작은 폰트의 부가 정보
- 너무 긴 문장
- 보정 후에도 의미 없는 텍스트"""
            
            user_prompt = f"""다음은 책 표지에서 OCR로 추출된 텍스트와 위치 정보입니다.
위치 정보를 활용하여 가장 책 제목일 확률이 높은 텍스트를 추출해주세요.

📖 **추출된 텍스트 (위치 정보 포함)**:
{text_with_boxes}

💡 **분석 가이드**:
1. **텍스트 보정**: 각 텍스트의 OCR 오타를 수정하고 정리
2. **위치 분석**: y값이 작을수록 상단에 위치
3. **크기 분석**: 바운딩 박스 크기가 클수록 중요한 텍스트
4. **신뢰도**: 높은 신뢰도 텍스트 우선 고려

⚠️ **중요**: 
- 설명이나 마커를 절대 포함하지 마세요
- "제목:", "추출:", "결과:" 등의 텍스트를 포함하지 마세요
- 따옴표나 특수문자를 포함하지 마세요
- 순수한 책 제목 텍스트만 반환하세요

예시:
❌ 잘못된 응답: "제목: 마음의 기술"
❌ 잘못된 응답: "추출된 책 제목: '우연한 일은'"
✅ 올바른 응답: "마음의 기술"
✅ 올바른 응답: "우연한 일은"

책 제목:"""
            
            # GPT API 호출
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,  # 토큰 수 증가 (보정 단계 추가)
                temperature=0.1
            )
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # 응답 추출
            gpt_response = response.choices[0].message.content
            usage = response.usage
            
            # 응답 후처리 - 책 제목 부분만 추출
            cleaned_response = self._extract_book_title_from_response(gpt_response)
            
            return GPTResponse(
                original_text=text_with_boxes,
                prompt="텍스트 보정 및 바운딩 박스 정보를 활용한 책 제목 추출",
                gpt_response=cleaned_response,
                gpt_model=self.model,
                tokens_used=usage.total_tokens if usage else 0,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            raise GPTException(f"바운딩 박스 정보를 활용한 책 제목 추출 실패: {str(e)}")
    
    def _extract_book_title_from_response(self, response: str) -> str:
        """GPT 응답에서 순수한 책 제목 텍스트만 추출"""
        if not response:
            return ""
        
        # 다양한 마커 패턴 제거 (더 포괄적으로)
        markers_to_remove = [
            "추출된 책 제목:",
            "책 제목:",
            "제목:",
            "**추출된 책 제목**:",
            "**책 제목**:",
            "**제목**:",
            "보정된 텍스트:",
            "분석:",
            "결과:",
            "최종:",
            "추정:",
            "추출:",
            "선택:",
            "결론:",
            "📖",
            "💡",
            "⚠️",
            "❌",
            "✅",
            "title:",
            "Title:",
            "TITLE:",
            "책제목:",
            "추출결과:",
            "최종결과:"
        ]
        
        # 마커 제거
        cleaned_response = response
        for marker in markers_to_remove:
            if marker in cleaned_response:
                # 마커 이후의 텍스트만 추출
                parts = cleaned_response.split(marker, 1)
                if len(parts) > 1:
                    cleaned_response = parts[1].strip()
        
        # 따옴표 제거 (모든 종류의 따옴표)
        cleaned_response = cleaned_response.strip('"\'`""''')
        
        # 줄바꿈 제거하고 첫 번째 줄만 추출
        lines = cleaned_response.split('\n')
        for line in lines:
            line = line.strip()
            if line and not any(marker in line for marker in markers_to_remove):
                # 특수문자 제거 (한글, 영어, 숫자, 공백만 허용)
                import re
                title = re.sub(r'[^\w\s가-힣]', '', line)
                title = re.sub(r'\s+', ' ', title).strip()
                
                if title:  # 빈 문자열이 아닌 경우만 반환
                    return title
        
        # 마커가 없는 경우 전체 텍스트에서 특수문자만 제거
        import re
        final_title = re.sub(r'[^\w\s가-힣]', '', cleaned_response)
        final_title = re.sub(r'\s+', ' ', final_title).strip()
        
        return final_title 