import api from './api.js';

// 세션 관리 관련 API 서비스
export const sessionService = {
    // 새 세션 생성
    createSession: async () => {
        const result = await api.post('/chat/session/new');
        return result;
    },

    // 세션 정보 조회
    getSessionInfo: async (sessionId) => {
        const result = await api.get(`/chat/session/${sessionId}/info`);
        return result;
    },

    // 세션 삭제
    deleteSession: async (sessionId) => {
        const result = await api.delete(`/chat/session/${sessionId}`);
        return result;
    },

    // 활성 세션 목록 조회
    getActiveSessions: async () => {
        const result = await api.get('/chat/sessions');
        return result;
    },

    // 모든 세션 삭제
    clearAllSessions: async () => {
        const result = await api.delete('/chat/sessions/clear');
        return result;
    }
};

// 로컬 스토리지 관련 유틸리티
export const sessionStorage = {
    // 세션 ID 저장
    saveSessionId: (sessionId) => {
        localStorage.setItem('chatbot_session_id', sessionId);
    },

    // 세션 ID 가져오기
    getSessionId: () => {
        return localStorage.getItem('chatbot_session_id');
    },

    // 세션 ID 삭제
    removeSessionId: () => {
        localStorage.removeItem('chatbot_session_id');
    },

    // 채팅 히스토리 저장
    saveChatHistory: (sessionId, history) => {
        localStorage.setItem(`chatbot_history_${sessionId}`, JSON.stringify(history));
    },

    // 채팅 히스토리 가져오기
    getChatHistory: (sessionId) => {
        const history = localStorage.getItem(`chatbot_history_${sessionId}`);
        return history ? JSON.parse(history) : [];
    },

    // 채팅 히스토리 삭제
    removeChatHistory: (sessionId) => {
        localStorage.removeItem(`chatbot_history_${sessionId}`);
    }
};

export default sessionService; 