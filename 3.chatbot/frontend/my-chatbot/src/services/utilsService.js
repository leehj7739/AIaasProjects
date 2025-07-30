import api from './api.js';

// 유틸리티 관련 API 서비스
export const utilsService = {
    // 데이터베이스 정보 조회
    getDatabaseInfo: async () => {
        const result = await api.get('/utils/database/info');
        return result;
    },

    // 스키마 정보 조회
    getSchemaInfo: async () => {
        const result = await api.get('/utils/schema/info');
        return result;
    },

    // 토큰 사용량 조회
    getTokenUsage: async () => {
        const result = await api.get('/utils/tokens/usage');
        return result;
    },

    // Cypher 쿼리 테스트
    testCypherQuery: async (query) => {
        const result = await api.post(`/utils/cypher/test?query=${encodeURIComponent(query)}`);
        return result;
    }
};

export default utilsService; 