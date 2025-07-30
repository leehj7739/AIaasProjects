import React, { useState, useEffect } from 'react';
import MainPage from './components/Pages/MainPage';
import LoadingPage from './components/Pages/LoadingPage';
import ChatContainer from './components/Pages/ChatContainer';
import { sessionService, sessionStorage, checkApiHealth } from './services';

function App() {
  const [currentPage, setCurrentPage] = useState('main'); // 'main', 'loading', 'chat'
  const [sessionId, setSessionId] = useState(null);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // API 연결 상태 확인
  useEffect(() => {
    const checkConnection = async () => {
      const isHealthy = await checkApiHealth();
      setIsConnected(isHealthy);
    };

    checkConnection();

    // 주기적으로 연결 상태 확인 (5분마다)
    const interval = setInterval(checkConnection, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 저장된 세션 ID 복원
  useEffect(() => {
    const savedSessionId = sessionStorage.getSessionId();
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  const handleNavigateToChat = async () => {
    setIsLoading(true);
    setCurrentPage('loading');

    try {
      // 새 세션 생성
      const result = await sessionService.createSession();

      if (result.success) {
        const newSessionId = result.data.session_id;
        setSessionId(newSessionId);
        setSessionInfo(result.data.session_info);

        // 로컬 스토리지에 저장
        sessionStorage.saveSessionId(newSessionId);

        setCurrentPage('chat');
      } else {
        console.error('세션 생성 실패:', result.error);
        // 에러 처리 - 메인 페이지로 돌아가기
        setCurrentPage('main');
      }
    } catch (error) {
      console.error('세션 생성 중 오류:', error);
      setCurrentPage('main');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadingComplete = () => {
    setCurrentPage('chat');
  };

  const handleBackToMain = () => {
    setCurrentPage('main');
  };

  const handleSessionReconnect = async () => {
    setIsLoading(true);

    try {
      // 기존 세션 삭제
      if (sessionId) {
        await sessionService.deleteSession(sessionId);
        sessionStorage.removeSessionId();
        sessionStorage.removeChatHistory(sessionId);
      }

      // 새 세션 생성
      const result = await sessionService.createSession();

      if (result.success) {
        const newSessionId = result.data.session_id;
        setSessionId(newSessionId);
        setSessionInfo(result.data.session_info);
        sessionStorage.saveSessionId(newSessionId);
      }
    } catch (error) {
      console.error('세션 재연결 중 오류:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'main':
        return <MainPage onNavigateToChat={handleNavigateToChat} isConnected={isConnected} />;
      case 'loading':
        return <LoadingPage onLoadingComplete={handleLoadingComplete} isLoading={isLoading} />;
      case 'chat':
        return (
          <ChatContainer
            onBackToMain={handleBackToMain}
            sessionId={sessionId}
            sessionInfo={sessionInfo}
            onSessionReconnect={handleSessionReconnect}
            isConnected={isConnected}
          />
        );
      default:
        return <MainPage onNavigateToChat={handleNavigateToChat} isConnected={isConnected} />;
    }
  };

  return (
    <div className="App">
      {renderCurrentPage()}
    </div>
  );
}

export default App;