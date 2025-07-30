import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from '../modules/ChatMessage';
import ChatInput from '../modules/ChatInput';
import { chatService, sessionStorage } from '../../services';

const initialBotMessage = {
  id: 1,
  from: 'bot',
  name: '영화챗봇',
  avatar: 'https://cdn.icon-icons.com/icons2/1371/PNG/512/robot02_90810.png',
  time: '',
  content: {
    text: '안녕하세요! 궁금한 영화를 물어보세요.',
    image: null
  }
};

export default function ChatContainer({
  onBackToMain,
  sessionId,
  sessionInfo,
  onSessionReconnect,
  isConnected
}) {
  const [messages, setMessages] = useState([initialBotMessage]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // 현재 시간 포맷팅 함수
  const getCurrentTime = () => {
    const now = new Date();
    return `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  };

  // 메시지 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 세션 ID가 변경될 때 채팅 히스토리 로드
  useEffect(() => {
    if (sessionId) {
      loadChatHistory();
      // 세션 정보 로깅 (개발용)
      if (sessionInfo) {
        console.log('세션 정보:', sessionInfo);
      }
    }
  }, [sessionId, sessionInfo]);

  // 채팅 히스토리 로드
  const loadChatHistory = async () => {
    try {
      // 로컬 스토리지에서 먼저 확인
      const localHistory = sessionStorage.getChatHistory(sessionId);

      if (localHistory && localHistory.length > 0) {
        setMessages(localHistory);
        return;
      }

      // 서버에서 히스토리 가져오기
      const result = await chatService.getChatHistory(sessionId);

      if (result.success && result.data) {
        // 서버 히스토리를 로컬 형식으로 변환
        const convertedHistory = convertServerHistoryToLocal(result.data);
        setMessages(convertedHistory);
        sessionStorage.saveChatHistory(sessionId, convertedHistory);
      } else {
        // 히스토리가 없으면 초기 메시지만 표시
        const initialMessage = {
          ...initialBotMessage,
          time: getCurrentTime()
        };
        setMessages([initialMessage]);
        sessionStorage.saveChatHistory(sessionId, [initialMessage]);
      }
    } catch (error) {
      console.error('채팅 히스토리 로드 실패:', error);
      setError('채팅 히스토리를 불러올 수 없습니다.');
    }
  };

  // 서버 히스토리를 로컬 형식으로 변환
  const convertServerHistoryToLocal = (serverHistory) => {
    // 서버 응답 형식에 따라 변환 로직 구현
    // 현재는 기본 형식으로 가정
    return serverHistory.map((msg, index) => ({
      id: index + 1,
      from: msg.from || 'bot',
      name: msg.name || (msg.from === 'bot' ? '영화챗봇' : '유저'),
      avatar: msg.avatar || (msg.from === 'bot' ? 'https://cdn.icon-icons.com/icons2/1371/PNG/512/robot02_90810.png' : 'https://i.pravatar.cc/100?img=7'),
      time: msg.time || getCurrentTime(),
      content: {
        text: msg.content?.text || msg.text || '',
        image: msg.content?.image || msg.image || null
      }
    }));
  };

  // 마크다운 텍스트에서 이미지 URL 추출
  const extractImagesFromMarkdown = (text) => {
    if (!text) return [];

    const imageRegex = /!\[.*?\]\((https?:\/\/[^\s)]+)\)/g;
    const images = [];
    let match;

    while ((match = imageRegex.exec(text)) !== null) {
      const imageUrl = match[1];
      // 중복 제거
      if (!images.includes(imageUrl)) {
        images.push(imageUrl);
      }
    }

    return images;
  };

  // 마크다운 텍스트 정리 (이미지 태그, 볼드 처리 제거)
  const cleanMarkdownText = (text) => {
    if (!text) return text;

    let cleanedText = text;

    // 이미지 마크다운 태그 제거 (더 정확한 패턴)
    cleanedText = cleanedText.replace(/!\[.*?\]\(https?:\/\/[^\s)]+\)/g, '');

    // 볼드 처리 제거 (**텍스트** → 텍스트)
    cleanedText = cleanedText.replace(/\*\*(.*?)\*\*/g, '$1');

    // 이모지와 특수문자 정리
    cleanedText = cleanedText.replace(/🎉|📚|✨|😊|msg-img/g, '');

    // 영화 제목 번호 패턴 정리 (1. **제목** → 1. 제목)
    cleanedText = cleanedText.replace(/(\d+\.)\s*\*\*(.*?)\*\*/g, '$1 $2');

    // 줄바꿈 추가: 번호 다음에 줄바꿈
    cleanedText = cleanedText.replace(/(\d+\.\s)/g, '\n$1');

    // 연속된 공백 정리 (줄바꿈은 유지)
    cleanedText = cleanedText.replace(/[ \t]+/g, ' ').trim();

    // 빈 줄 제거
    cleanedText = cleanedText.replace(/\n\s*\n/g, '\n');

    // 끝부분 정리
    cleanedText = cleanedText.replace(/\s*\/\/\/\/\/.*$/g, ''); // msg-img ///// 제거

    return cleanedText;
  };

  // 메시지 전송
  const handleSend = async () => {
    if (!input.trim() || isLoading || !isConnected) return;

    const userMessage = {
      id: messages.length + 1,
      from: 'user',
      name: '홍길동', // 또는 '유저'로 유지
      avatar: 'https://i.pravatar.cc/100?img=7',
      time: getCurrentTime(),
      content: {
        text: input,
        image: null
      }
    };

    // 사용자 메시지 추가
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);
    setError(null);

    // 로딩 메시지 추가
    const loadingMessage = {
      id: updatedMessages.length + 1,
      from: 'bot',
      name: '영화챗봇',
      avatar: 'https://cdn.icon-icons.com/icons2/1371/PNG/512/robot02_90810.png',
      time: getCurrentTime(),
      content: {
        text: '영화 정보를 찾고 있어요...',
        image: null
      }
    };

    setMessages(prev => [...prev, loadingMessage]);

    try {
      // API로 메시지 전송
      const result = await chatService.sendMessage(input, sessionId);

      // 개발 모드에서 예시 응답 사용 (테스트용)
      // const result = {
      //   success: true,
      //   data: {
      //     answer: "테스트 응답입니다! 영화 추천을 받으셨네요.",
      //     session_id: sessionId,
      //     posters: ["https://via.placeholder.com/300x450?text=Movie+1", "https://via.placeholder.com/300x450?text=Movie+2"]
      //   }
      // };

      if (result.success) {
        // 마크다운 텍스트에서 이미지 URL 추출
        const extractedImages = extractImagesFromMarkdown(result.data.answer);
        const cleanText = cleanMarkdownText(result.data.answer);

        // 디버깅용 로그
        console.log('원본 텍스트:', result.data.answer);
        console.log('정리된 텍스트:', cleanText);
        console.log('추출된 이미지:', extractedImages);

        // 백엔드에서 제공하는 posters 배열과 추출한 이미지 URL 결합
        const allImages = [
          ...(result.data.posters || []),
          ...extractedImages
        ].filter((url, index, arr) => arr.indexOf(url) === index); // 중복 제거

        const botResponse = {
          id: updatedMessages.length + 1,
          from: 'bot',
          name: '영화챗봇',
          avatar: 'https://cdn.icon-icons.com/icons2/1371/PNG/512/robot02_90810.png',
          time: getCurrentTime(),
          content: {
            text: cleanText,
            image: allImages.length > 0 ? allImages : null
          }
        };

        // 로딩 메시지를 실제 응답으로 교체
        const finalMessages = [...updatedMessages, botResponse];
        setMessages(finalMessages);

        // 로컬 스토리지에 저장
        sessionStorage.saveChatHistory(sessionId, finalMessages);
      } else {
        // 에러 메시지 표시
        const errorMessage = {
          id: updatedMessages.length + 1,
          from: 'bot',
          name: '영화챗봇',
          avatar: 'https://cdn.icon-icons.com/icons2/1371/PNG/512/robot02_90810.png',
          time: getCurrentTime(),
          content: {
            text: '죄송합니다. 응답을 받지 못했습니다. 다시 시도해주세요.',
            image: null
          }
        };

        const finalMessages = [...updatedMessages, errorMessage];
        setMessages(finalMessages);
        setError(result.error || '메시지 전송에 실패했습니다.');
      }
    } catch (error) {
      console.error('메시지 전송 오류:', error);

      const errorMessage = {
        id: updatedMessages.length + 1,
        from: 'bot',
        name: '영화챗봇',
        avatar: 'https://cdn.icon-icons.com/icons2/1371/PNG/512/robot02_90810.png',
        time: getCurrentTime(),
        content: {
          text: '네트워크 오류가 발생했습니다. 연결을 확인해주세요.',
          image: null
        }
      };

      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      setError('네트워크 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleReconnect = async () => {
    if (onSessionReconnect) {
      await onSessionReconnect();
    }
  };

  // 연결 상태에 따른 헤더 색상
  const headerBgColor = isConnected ? 'bg-teal-500' : 'bg-red-500';

  // 세션 정보 표시용 텍스트
  const getSessionInfoText = () => {
    if (!sessionInfo) return '새 세션';
    if (sessionInfo.created_at) return '활성 세션';
    if (sessionInfo.user_id) return '사용자 세션';
    if (sessionInfo.model_info) return 'AI 모델 준비됨';
    return '세션 정보';
  };

  // 세션 생성 시간 표시
  const getSessionTime = () => {
    if (!sessionInfo || !sessionInfo.created_at) return '';
    try {
      const createdTime = new Date(sessionInfo.created_at);
      return `${createdTime.getHours().toString().padStart(2, '0')}:${createdTime.getMinutes().toString().padStart(2, '0')}`;
    } catch (error) {
      console.error('세션 생성 시간 파싱 오류:', error);
      return '';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-2">
      <div className="w-full max-w-[480px] h-[90vh] sm:h-[640px] bg-white flex flex-col rounded-xl shadow-lg overflow-hidden border border-gray-200 mx-auto">
        {/* Header */}
        <div className={`${headerBgColor} flex items-center justify-between px-4 py-3`}>
          {/* 좌측: 뒤로가기 버튼 + 제목 */}
          <div className="flex items-center">
            <button
              onClick={onBackToMain}
              className="mr-3 p-1 rounded-full hover:bg-white hover:bg-opacity-20 transition-colors duration-200"
              title="메인으로 돌아가기"
            >
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <svg className="w-6 h-6 text-white mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h10a4 4 0 004-4V7a4 4 0 00-4-4H7a4 4 0 00-4 4v8z" />
            </svg>
            <span className="text-white font-bold text-lg">ChatBot</span>
            {!isConnected && (
              <span className="ml-2 text-white text-xs bg-red-600 px-2 py-1 rounded">연결 끊김</span>
            )}
          </div>

          {/* 중앙: 세션 정보 */}
          <div className="flex items-center">
            <span className="text-white text-xs mr-2">Session:</span>
            <div className="flex flex-col items-center">
              <input
                type="text"
                value={sessionId || '연결 중...'}
                readOnly
                className="bg-white bg-opacity-20 text-white text-xs px-2 py-1 rounded border border-white border-opacity-30 w-24 cursor-default text-center mb-1"
                placeholder="Session ID"
              />
              <span className="text-white text-xs opacity-75">{getSessionInfoText()}</span>
              {getSessionTime() && (
                <span className="text-white text-xs opacity-50">{getSessionTime()}</span>
              )}
            </div>
          </div>

          {/* 우측: 재접속 버튼 */}
          <button
            onClick={handleReconnect}
            disabled={isLoading}
            className={`bg-white bg-opacity-20 hover:bg-opacity-30 text-white text-xs px-2 py-1 rounded border border-white border-opacity-30 transition-all duration-200 flex items-center ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            title="재접속"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {isLoading ? '연결 중...' : '재접속'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 text-sm">
            {error}
          </div>
        )}

        {/* Chat List */}
        <div className="flex-1 bg-sky-200 px-3 py-2 overflow-y-auto flex flex-col gap-4">
          {messages.map(msg => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          input={input}
          onChange={handleInputChange}
          onSend={handleSend}
          disabled={isLoading || !isConnected}
        />
      </div>
    </div>
  );
}
