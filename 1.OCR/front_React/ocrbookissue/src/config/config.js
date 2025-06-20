// 환경변수 설정
const config = {
  // FastAPI 서버 URL - 환경변수에서 가져오거나 기본값 사용
  FASTAPI_BASE_URL: process.env.REACT_APP_FASTAPI_BASE_URL || 'http://192.168.45.120:8000',
  
  // 개발 환경 여부
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  
  // API 타임아웃 설정 (밀리초)
  API_TIMEOUT: 30000,
  
  // 이미지 리사이즈 설정
  IMAGE_RESIZE: {
    MAX_WIDTH: 1200,
    MAX_HEIGHT: 1600,
    QUALITY: 0.85
  }
};

// 개발 환경에서 설정값 로깅
if (config.IS_DEVELOPMENT) {
  console.log('🔧 환경 설정:', {
    FASTAPI_BASE_URL: config.FASTAPI_BASE_URL,
    NODE_ENV: process.env.NODE_ENV,
    REACT_APP_FASTAPI_BASE_URL: process.env.REACT_APP_FASTAPI_BASE_URL
  });
}

export default config; 