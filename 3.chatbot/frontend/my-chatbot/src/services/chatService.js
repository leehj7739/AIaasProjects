import api from './api.js';

// 채팅 관련 API 서비스
export const chatService = {
    // 새 세션 생성
    createSession: async () => {
        const result = await api.post('/chat/session/new');
        return result;
    },

    // 메시지 전송
    sendMessage: async (message, sessionId = null) => {
        const requestData = {
            message: message,
            session_id: sessionId
        };

        const result = await api.post('/chat/send', requestData);
        return result;
    },

    // 채팅 히스토리 조회
    getChatHistory: async (sessionId) => {
        const result = await api.get(`/chat/history/${sessionId}`);
        return result;
    },

    // 채팅 히스토리 초기화
    clearChatHistory: async (sessionId) => {
        const result = await api.delete(`/chat/history/${sessionId}`);
        return result;
    },

    // 활성 세션 목록 조회
    getActiveSessions: async () => {
        const result = await api.get('/chat/sessions');
        return result;
    },

    // 특정 세션 정보 조회
    getSessionInfo: async (sessionId) => {
        const result = await api.get(`/chat/session/${sessionId}/info`);
        return result;
    },

    // 특정 세션 삭제
    deleteSession: async (sessionId) => {
        const result = await api.delete(`/chat/session/${sessionId}`);
        return result;
    },

    // 모든 세션 삭제
    clearAllSessions: async () => {
        const result = await api.delete('/chat/sessions/clear');
        return result;
    },

    // 챗봇 상태 확인
    checkHealth: async () => {
        const result = await api.get('/chat/health');
        return result;
    }
};

export default chatService; 