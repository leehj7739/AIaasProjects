// API 기본 설정
const API_BASE_URL = 'http://127.0.0.1:8000';

// 기본 헤더 설정
const getDefaultHeaders = () => ({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
});

// 공통 API 호출 함수
const apiCall = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            ...getDefaultHeaders(),
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('API 호출 오류:', error);
        return {
            success: false,
            error: error.message || '알 수 없는 오류가 발생했습니다.'
        };
    }
};

// HTTP 메서드별 헬퍼 함수들
export const api = {
    get: (endpoint, options = {}) =>
        apiCall(endpoint, { ...options, method: 'GET' }),

    post: (endpoint, data, options = {}) =>
        apiCall(endpoint, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        }),

    put: (endpoint, data, options = {}) =>
        apiCall(endpoint, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    delete: (endpoint, options = {}) =>
        apiCall(endpoint, { ...options, method: 'DELETE' }),
};

// API 상태 확인
export const checkApiHealth = async () => {
    const result = await api.get('/chat/health');
    return result.success;
};

export default api; 