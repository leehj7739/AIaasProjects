import axios from 'axios';
import xml2js from 'xml2js';

// 환경 변수에서 API 설정 가져오기
const API_KEY = process.env.REACT_APP_API_KEY;
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://data4library.kr';

// FastAPI 서버 URL
const FASTAPI_BASE_URL = 'http://192.168.45.120:8000';

// 캐시 설정
const CACHE_DURATION = 60 * 60 * 1000; // 1시간 (밀리초)
const CACHE_KEY = 'library_cache';

// 메모리 캐시
const memoryCache = new Map();

// 병렬 처리를 위한 유틸리티 함수들
const parallelUtils = {
  // 배치 크기별로 배열을 나누는 함수
  chunkArray: (array, chunkSize) => {
    const chunks = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    return chunks;
  },

  // 동시 요청 수를 제한하는 함수
  limitConcurrency: async (tasks, maxConcurrency = 5) => {
    const startTime = Date.now();
    const results = [];
    const executing = [];

    for (const task of tasks) {
      const promise = task();
      results.push(promise);

      if (maxConcurrency <= tasks.length) {
        const clean = () => executing.splice(executing.indexOf(clean), 1);
        executing.push(clean);
        promise.then(clean).catch(clean);
      }

      if (executing.length >= maxConcurrency) {
        await Promise.race(executing);
      }
    }

    const finalResults = await Promise.all(results);
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    console.log(`⚡ 병렬 처리 완료: ${tasks.length}개 작업, ${duration}ms 소요 (동시성: ${maxConcurrency})`);
    
    return finalResults;
  },

  // 재시도 로직이 포함된 병렬 처리
  retryParallel: async (tasks, maxRetries = 3, delay = 1000) => {
    const startTime = Date.now();
    const results = await Promise.allSettled(tasks);
    
    const failedTasks = results
      .map((result, index) => ({ result, index, task: tasks[index] }))
      .filter(({ result }) => result.status === 'rejected');

    if (failedTasks.length === 0 || maxRetries <= 0) {
      const endTime = Date.now();
      const duration = endTime - startTime;
      console.log(`⚡ 재시도 병렬 처리 완료: ${tasks.length}개 작업, ${duration}ms 소요`);
      return results;
    }

    console.log(`🔄 ${failedTasks.length}개 작업 재시도 중... (남은 시도: ${maxRetries})`);
    
    // 재시도 전 잠시 대기
    await new Promise(resolve => setTimeout(resolve, delay));

    const retryTasks = failedTasks.map(({ task }) => task);
    const retryResults = await parallelUtils.retryParallel(retryTasks, maxRetries - 1, delay * 1.5);

    // 원래 결과와 재시도 결과 병합
    let retryIndex = 0;
    const finalResults = results.map((result, index) => {
      if (result.status === 'rejected' && retryIndex < retryResults.length) {
        return retryResults[retryIndex++];
      }
      return result;
    });

    const endTime = Date.now();
    const duration = endTime - startTime;
    console.log(`⚡ 재시도 병렬 처리 완료: ${tasks.length}개 작업, ${duration}ms 소요`);
    
    return finalResults;
  },

  // 성능 모니터링 함수
  measurePerformance: (name, fn) => {
    return async (...args) => {
      const startTime = Date.now();
      const startMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;
      
      try {
        const result = await fn(...args);
        const endTime = Date.now();
        const endMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;
        const duration = endTime - startTime;
        const memoryUsed = endMemory - startMemory;
        
        console.log(`📊 성능 측정 [${name}]: ${duration}ms, 메모리: ${(memoryUsed / 1024 / 1024).toFixed(2)}MB`);
        
        return result;
      } catch (error) {
        const endTime = Date.now();
        const duration = endTime - startTime;
        console.error(`❌ 성능 측정 [${name}] 실패: ${duration}ms`, error);
        throw error;
      }
    };
  }
};

// 캐시 유틸리티 함수들
const cacheUtils = {
  // 캐시 키 생성
  generateCacheKey: (pageNo, pageSize) => `library_${pageNo}_${pageSize}`,
  
  // 메모리 캐시에서 데이터 가져오기
  getFromMemory: (key) => {
    const cached = memoryCache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      console.log('💾 메모리 캐시에서 데이터 로드:', key);
      return cached.data;
    }
    memoryCache.delete(key);
    return null;
  },
  
  // 메모리 캐시에 데이터 저장
  setToMemory: (key, data) => {
    memoryCache.set(key, {
      data,
      timestamp: Date.now()
    });
    console.log('💾 메모리 캐시에 데이터 저장:', key);
  },
  
  // 로컬 스토리지에서 데이터 가져오기
  getFromStorage: (key) => {
    try {
      const cached = localStorage.getItem(key);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Date.now() - parsed.timestamp < CACHE_DURATION) {
          console.log('💾 로컬 스토리지에서 데이터 로드:', key);
          return parsed.data;
        }
        localStorage.removeItem(key);
      }
    } catch (error) {
      console.error('로컬 스토리지 읽기 에러:', error);
    }
    return null;
  },
  
  // 로컬 스토리지에 데이터 저장
  setToStorage: (key, data) => {
    try {
      localStorage.setItem(key, JSON.stringify({
        data,
        timestamp: Date.now()
      }));
      console.log('💾 로컬 스토리지에 데이터 저장:', key);
    } catch (error) {
      console.error('로컬 스토리지 저장 에러:', error);
    }
  },
  
  // 캐시 정리 (만료된 데이터 삭제)
  cleanup: () => {
    const now = Date.now();
    
    // 메모리 캐시 정리
    for (const [key, value] of memoryCache.entries()) {
      if (now - value.timestamp > CACHE_DURATION) {
        memoryCache.delete(key);
      }
    }
    
    // 로컬 스토리지 정리
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith('library_')) {
          const cached = localStorage.getItem(key);
          if (cached) {
            const parsed = JSON.parse(cached);
            if (now - parsed.timestamp > CACHE_DURATION) {
              localStorage.removeItem(key);
            }
          }
        }
      });
    } catch (error) {
      console.error('캐시 정리 에러:', error);
    }
  }
};

// XML 파서 설정
const parser = new xml2js.Parser({
  explicitArray: false,
  ignoreAttrs: true
});

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
  },
});

// 요청 인터셉터 (요청 전에 실행)
api.interceptors.request.use(
  (config) => {
    console.log('API 요청:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API 요청 에러:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (응답 후에 실행)
api.interceptors.response.use(
  (response) => {
    console.log('API 응답:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API 응답 에러:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// FastAPI 서버 헬스체크 함수
const healthCheck = {
  // 기본 헬스체크
  checkHealth: async () => {
    try {
      console.log('🔍 FastAPI 서버 헬스체크 시작...');
      const startTime = Date.now();
      
      const response = await axios.get(`${FASTAPI_BASE_URL}/api/health`, {
        timeout: 5000, // 5초 타임아웃
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      console.log(`✅ FastAPI 서버 헬스체크 성공: ${responseTime}ms`);
      
      return {
        status: 'healthy',
        data: response.data,
        responseTime: `${responseTime}ms`,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ FastAPI 서버 헬스체크 실패:', error.message);
      
      let errorDetails = {
        message: error.message,
        code: error.code || 'UNKNOWN'
      };
      
      if (error.response) {
        errorDetails.statusCode = error.response.status;
        errorDetails.statusText = error.response.statusText;
        errorDetails.data = error.response.data;
      } else if (error.request) {
        errorDetails.type = 'NETWORK_ERROR';
        errorDetails.details = '서버에 연결할 수 없습니다';
      }
      
      return {
        status: 'unhealthy',
        error: errorDetails,
        timestamp: new Date().toISOString()
      };
    }
  }
};

// API 함수들
export const apiService = {
  // OCR + GPT 통합 이미지 업로드 (FastAPI /extract-and-analyze 엔드포인트)
  uploadImage: async (imageFile, mode = "prod", gptPrompt = "책 제목 추출") => {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('mode', mode);
    formData.append('gpt_prompt', gptPrompt);
    
    console.log('📤 이미지 업로드 시작:', {
      fileName: imageFile.name,
      fileSize: imageFile.size,
      mode: mode,
      gptPrompt: gptPrompt
    });
    
    return axios.post(`${FASTAPI_BASE_URL}/api/ocr/extract-and-analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60초 타임아웃 (OCR + GPT 처리 시간 고려)
    });
  },

  // 책 정보 가져오기
  getBookInfo: async (isbn) => {
    return api.get(`/books/${isbn}`);
  },

  // 사용자 정보 가져오기
  getUserInfo: async () => {
    return api.get('/user/profile');
  },

  // 가격 정보 가져오기
  getPricing: async () => {
    return api.get('/pricing');
  },

  // 라이브러리 목록 가져오기 (캐싱 적용)
  getLibrary: async (pageNo = 1, pageSize = 20, ignoreCache = false) => {
    const cacheKey = cacheUtils.generateCacheKey(pageNo, pageSize);
    
    // 캐시 무시 옵션이 false인 경우에만 캐시 확인
    if (!ignoreCache) {
      // 1. 메모리 캐시 확인
      let cachedData = cacheUtils.getFromMemory(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // 2. 로컬 스토리지 캐시 확인
      cachedData = cacheUtils.getFromStorage(cacheKey);
      if (cachedData) {
        // 메모리 캐시에도 저장
        cacheUtils.setToMemory(cacheKey, cachedData);
        return cachedData;
      }
    } else {
      console.log("🔄 캐시 무시하고 새로운 데이터 요청:", cacheKey);
    }
    
    // 3. API 호출
    const apiKey = process.env.REACT_APP_LIBRARY_API_KEY || 'test_api_key_123';
    
    console.log("🔍 도서관 API 호출 (캐시 미스):", cacheKey);
    console.log("API 키:", apiKey);
    
    try {
      const response = await axios.get(`http://data4library.kr/api/libSrch`, {
        params: {
          authKey: apiKey,
          pageNo,
          pageSize
        },
        timeout: 15000,
        headers: {
          'Accept': 'application/xml, text/xml, */*',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log("📄 XML 응답 받음:", response.data);
      
      // XML을 JSON으로 파싱
      const result = await parser.parseStringPromise(response.data);
      console.log("🔄 파싱된 JSON:", result);
      
      // 실제 API 응답 구조에 맞게 데이터 추출
      const libs = result.response?.libs?.lib || [];
      const totalCount = result.response?.numFound || 0;
      const currentCount = result.response?.resultNum || 0;
      
      console.log(`📊 총 ${totalCount}개 중 ${currentCount}개 로드됨`);
      
      const responseData = {
        data: {
          response: {
            libs: libs,
            numFound: totalCount,
            resultNum: currentCount
          }
        }
      };
      
      // 캐시에 저장
      cacheUtils.setToMemory(cacheKey, responseData);
      cacheUtils.setToStorage(cacheKey, responseData);
      
      return responseData;
      
    } catch (error) {
      console.error('도서관 API 호출 실패:', error);
      
      // CORS 에러인 경우 프록시 사용
      if (error.code === 'ERR_NETWORK' || error.message.includes('CORS')) {
        console.log("🔄 CORS 에러 - 프록시 사용");
        const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
        const targetUrl = `http://data4library.kr/api/libSrch?authKey=${apiKey}&pageNo=${pageNo}&pageSize=${pageSize}`;
        
        try {
          const proxyResponse = await axios.get(proxyUrl + targetUrl, {
            timeout: 15000,
            headers: {
              'Origin': 'http://localhost:3000',
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/xml, text/xml, */*'
            }
          });
          
          console.log("📄 프록시 XML 응답:", proxyResponse.data);
          
          // XML을 JSON으로 파싱
          const proxyResult = await parser.parseStringPromise(proxyResponse.data);
          console.log("🔄 프록시 파싱된 JSON:", proxyResult);
          
          // 실제 API 응답 구조에 맞게 데이터 추출
          const proxyLibs = proxyResult.response?.libs?.lib || [];
          const proxyTotalCount = proxyResult.response?.numFound || 0;
          const proxyCurrentCount = proxyResult.response?.resultNum || 0;
          
          console.log(`📊 총 ${proxyTotalCount}개 중 ${proxyCurrentCount}개 로드됨`);
          
          const proxyResponseData = {
            data: {
              response: {
                libs: proxyLibs,
                numFound: proxyTotalCount,
                resultNum: proxyCurrentCount
              }
            }
          };
          
          // 캐시에 저장
          cacheUtils.setToMemory(cacheKey, proxyResponseData);
          cacheUtils.setToStorage(cacheKey, proxyResponseData);
          
          return proxyResponseData;
        } catch (proxyError) {
          console.error('프록시 호출도 실패:', proxyError);
        }
      }
      
      // 에러 시 더미 데이터 반환
      console.log("⚠️ 에러 발생 - 더미 데이터 사용");
      return {
        data: {
          response: {
            libs: [
              {
                libName: "서울도서관",
                address: "서울특별시 중구 세종대로 110",
                phone: "02-2133-0300",
                region: "서울",
                hours: "월~금 09:00~21:00, 토~일 09:00~18:00",
                homepage: "https://lib.seoul.go.kr/",
                libCode: "SEOUL001"
              },
              {
                libName: "경기중앙도서관",
                address: "경기도 수원시 팔달구 효원로 293",
                phone: "031-228-4746",
                region: "경기",
                hours: "매일 09:00~22:00",
                homepage: "https://www.janganlib.or.kr/",
                libCode: "GYEONGGI001"
              },
              {
                libName: "부산시립도서관",
                address: "부산광역시 남구 유엔평화로 76",
                phone: "051-810-8200",
                region: "부산",
                hours: "화~일 09:00~18:00",
                homepage: "https://www.busan.go.kr/library/",
                libCode: "BUSAN001"
              }
            ],
            numFound: 3,
            resultNum: 3
          }
        }
      };
    }
  },

  // 캐시 정리 함수
  clearCache: () => {
    memoryCache.clear();
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith('library_')) {
          localStorage.removeItem(key);
        }
      });
      console.log('🗑️ 캐시 정리 완료');
    } catch (error) {
      console.error('캐시 정리 에러:', error);
    }
  },

  // 캐시 상태 확인
  getCacheStatus: () => {
    const memorySize = memoryCache.size;
    let storageSize = 0;
    try {
      const keys = Object.keys(localStorage);
      storageSize = keys.filter(key => key.startsWith('library_')).length;
    } catch (error) {
      console.error('캐시 상태 확인 에러:', error);
    }
    
    return {
      memoryCacheSize: memorySize,
      storageCacheSize: storageSize,
      cacheDuration: CACHE_DURATION / (60 * 60 * 1000) // 시간 단위
    };
  },

  // ISBN 상세조회 API
  getBookByISBN: async (isbn) => {
    const apiKey = process.env.REACT_APP_LIBRARY_API_KEY || 'test_api_key_123';
    
    console.log("🔍 ISBN 상세조회 API 호출:", isbn);
    
    try {
      const response = await axios.get(`http://data4library.kr/api/srchDtlList`, {
        params: {
          authKey: apiKey,
          isbn13: isbn,
          loaninfoYN: 'Y',
          displayInfo: 'age'
        },
        timeout: 15000,
        headers: {
          'Accept': 'application/xml, text/xml, */*',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log("📄 ISBN 상세조회 XML 응답:", response.data);
      
      // XML을 JSON으로 파싱
      const result = await parser.parseStringPromise(response.data);
      console.log("🔄 파싱된 JSON:", result);
      
      return {
        data: {
          response: result.response
        }
      };
      
    } catch (error) {
      console.error('ISBN 상세조회 API 호출 실패:', error);
      
      // CORS 에러인 경우 프록시 사용
      if (error.code === 'ERR_NETWORK' || error.message.includes('CORS')) {
        console.log("🔄 CORS 에러 - 프록시 사용");
        const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
        const targetUrl = `http://data4library.kr/api/srchDtlList?authKey=${apiKey}&isbn13=${isbn}&loaninfoYN=Y&displayInfo=age`;
        
        try {
          const proxyResponse = await axios.get(proxyUrl + targetUrl, {
            timeout: 15000,
            headers: {
              'Origin': 'http://localhost:3000',
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/xml, text/xml, */*'
            }
          });
          
          console.log("📄 프록시 ISBN 상세조회 XML 응답:", proxyResponse.data);
          
          // XML을 JSON으로 파싱
          const proxyResult = await parser.parseStringPromise(proxyResponse.data);
          console.log("🔄 프록시 파싱된 JSON:", proxyResult);
          
          return {
            data: {
              response: proxyResult.response
            }
          };
        } catch (proxyError) {
          console.error('프록시 ISBN 상세조회 호출도 실패:', proxyError);
        }
      }
      
      // 에러 시 더미 데이터 반환
      console.log("⚠️ 에러 발생 - 더미 ISBN 데이터 사용");
      return {
        data: {
          response: {
            detail: [{
              book: {
                bookname: "위버멘쉬",
                authors: "프리드리히 니체",
                publisher: "더클래식",
                bookImageURL: "/dummy-image.png",
                description: "누구의 시선도 아닌, 내 의지대로 살겠다는 선언",
                isbn13: isbn,
                publication_year: "2023"
              }
            }],
            loanInfo: {
              Total: {
                ranking: "1",
                name: "전체",
                loanCnt: "100"
              }
            }
          }
        }
      };
    }
  },

  // 키워드 기반 도서 검색 API
  searchBooksByKeyword: async (keyword, pageNo = 1, pageSize = 10) => {
    const apiKey = process.env.REACT_APP_LIBRARY_API_KEY || 'test_api_key_123';
    
    // API 키가 테스트 키인지 확인
    const isTestKey = apiKey === 'test_api_key_123';
    if (isTestKey) {
      console.warn("⚠️ 테스트 API 키 사용 중 - 실제 API 호출이 실패할 수 있습니다.");
    }
    
    // 키워드 전처리: 앞의 두 단어만 추출
    const processKeyword = (keyword) => {
      const words = keyword.trim().split(/\s+/).filter(word => word.length > 0);
      return words.slice(0, 2).join(' ');
    };
    
    const processedKeyword = processKeyword(keyword);
    
    console.log("🔍 키워드 도서 검색 API 호출:", keyword);
    console.log("📝 전처리된 키워드 (앞 2단어):", processedKeyword);
    console.log("🔑 API 키:", isTestKey ? "테스트 키 (실제 API 호출 실패 예상)" : "실제 키");
    
    try {
      // 항상 앞의 두 단어만 keyword로 사용
      const response = await axios.get(`http://data4library.kr/api/srchBooks`, {
        params: {
          authKey: apiKey,
          keyword: processedKeyword,
          pageNo,
          pageSize
        },
        timeout: 15000,
        headers: {
          'Accept': 'application/xml, text/xml, */*',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log("📄 키워드 검색 XML 응답:", response.data);
      
      // XML을 JSON으로 파싱
      const result = await parser.parseStringPromise(response.data);
      console.log("🔄 파싱된 JSON:", result);
      
      return {
        data: {
          response: result.response
        }
      };
      
    } catch (error) {
      console.error('키워드 도서 검색 API 호출 실패:', error);
      console.error('에러 상세 정보:', {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      });
      
      // CORS 에러인 경우 프록시 사용
      if (error.code === 'ERR_NETWORK' || error.message.includes('CORS')) {
        console.log("🔄 CORS 에러 - 프록시 사용");
        
        // 단일 키워드 프록시 URL
        const targetUrl = `http://data4library.kr/api/srchBooks?authKey=${apiKey}&keyword=${encodeURIComponent(processedKeyword)}&pageNo=${pageNo}&pageSize=${pageSize}`;
        
        console.log("🔗 프록시 URL:", targetUrl);
        const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
        
        try {
          const proxyResponse = await axios.get(proxyUrl + targetUrl, {
            timeout: 15000,
            headers: {
              'Origin': 'http://localhost:3000',
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/xml, text/xml, */*'
            }
          });
          
          console.log("📄 프록시 키워드 검색 XML 응답:", proxyResponse.data);
          
          // XML을 JSON으로 파싱
          const proxyResult = await parser.parseStringPromise(proxyResponse.data);
          console.log("🔄 프록시 파싱된 JSON:", proxyResult);
          
          return {
            data: {
              response: proxyResult.response
            }
          };
        } catch (proxyError) {
          console.error('프록시 키워드 검색 호출도 실패:', proxyError);
          console.error('프록시 에러 상세 정보:', {
            message: proxyError.message,
            code: proxyError.code,
            status: proxyError.response?.status,
            statusText: proxyError.response?.statusText,
            data: proxyError.response?.data
          });
        }
      }
      // 에러 시 빈 결과 반환
      console.log("⚠️ API 호출 실패 - 검색 결과 없음");
      return {
        data: {
          response: {
            docs: [],
            numFound: 0,
            resultNum: 0
          }
        }
      };
    }
  },

  // 제목 기반 도서 검색 API
  searchBooksByTitle: async (title, pageNo = 1, pageSize = 10) => {
    const apiKey = process.env.REACT_APP_LIBRARY_API_KEY || 'test_api_key_123';
    
    console.log("🔍 제목 도서 검색 API 호출:", title);
    
    try {
      const response = await axios.get(`http://data4library.kr/api/srchBooks`, {
        params: {
          authKey: apiKey,
          title: title,
          pageNo,
          pageSize,
          searchTarget: 'bookname'
        },
        timeout: 15000,
        headers: {
          'Accept': 'application/xml, text/xml, */*',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log("📄 제목 검색 XML 응답:", response.data);
      
      // XML을 JSON으로 파싱
      const result = await parser.parseStringPromise(response.data);
      console.log("🔄 파싱된 JSON:", result);
      
      if (result.response?.docs?.doc) {
        const books = Array.isArray(result.response.docs.doc) 
          ? result.response.docs.doc 
          : [result.response.docs.doc];
        
        const filteredBooks = books.filter(book => {
          const bookTitle = book.bookname?.toLowerCase() || '';
          const searchTitle = title.toLowerCase();
          return bookTitle.includes(searchTitle) || searchTitle.includes(bookTitle);
        });
        
        result.response.docs.doc = filteredBooks;
        result.response.numFound = filteredBooks.length.toString();
        result.response.resultNum = filteredBooks.length.toString();
      }
      
      return {
        data: {
          response: result.response
        }
      };
      
    } catch (error) {
      console.error('제목 도서 검색 API 호출 실패:', error);
      
      // CORS 에러인 경우 프록시 사용
      if (error.code === 'ERR_NETWORK' || error.message.includes('CORS')) {
        console.log("🔄 CORS 에러 - 프록시 사용");
        const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
        const targetUrl = `http://data4library.kr/api/srchBooks?authKey=${apiKey}&title=${encodeURIComponent(title)}&pageNo=${pageNo}&pageSize=${pageSize}&searchTarget=bookname`;
        
        try {
          const proxyResponse = await axios.get(proxyUrl + targetUrl, {
            timeout: 15000,
            headers: {
              'Origin': 'http://localhost:3000',
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/xml, text/xml, */*'
            }
          });
          
          console.log("📄 프록시 제목 검색 XML 응답:", proxyResponse.data);
          
          // XML을 JSON으로 파싱
          const proxyResult = await parser.parseStringPromise(proxyResponse.data);
          console.log("🔄 프록시 파싱된 JSON:", proxyResult);
          
          if (proxyResult.response?.docs?.doc) {
            const proxyBooks = Array.isArray(proxyResult.response.docs.doc) 
              ? proxyResult.response.docs.doc 
              : [proxyResult.response.docs.doc];
            
            const filteredProxyBooks = proxyBooks.filter(book => {
              const bookTitle = book.bookname?.toLowerCase() || '';
              const searchTitle = title.toLowerCase();
              return bookTitle.includes(searchTitle) || searchTitle.includes(bookTitle);
            });
            
            proxyResult.response.docs.doc = filteredProxyBooks;
            proxyResult.response.numFound = filteredProxyBooks.length.toString();
            proxyResult.response.resultNum = filteredProxyBooks.length.toString();
          }
          
          return {
            data: {
              response: proxyResult.response
            }
          };
        } catch (proxyError) {
          console.error('프록시 제목 검색 호출도 실패:', proxyError);
        }
      }
      
      // 에러 시 더미 데이터 반환
      console.log("⚠️ 에러 발생 - 더미 제목 검색 데이터 사용");
      return {
        data: {
          response: {
            docs: [
              {
                doc: {
                  bookname: "위버멘쉬",
                  authors: "프리드리히 니체",
                  publisher: "더클래식",
                  bookImageURL: "/dummy-image.png",
                  description: "누구의 시선도 아닌, 내 의지대로 살겠다는 선언",
                  isbn13: "9788960861234"
                }
              },
              {
                doc: {
                  bookname: "데미안",
                  authors: "헤르만 헤세",
                  publisher: "민음사",
                  bookImageURL: "https://image.aladin.co.kr/product/32425/0/cover500/k112939963_1.jpg",
                  description: "자아를 찾아가는 성장의 여정",
                  isbn13: "9788937473456"
                }
              },
              {
                doc: {
                  bookname: "호밀밭의 파수꾼",
                  authors: "J.D. 샐린저",
                  publisher: "민음사",
                  bookImageURL: "https://image.aladin.co.kr/product/32425/0/cover500/k112939963_2.jpg",
                  description: "청춘의 방황과 진실에 대한 갈망",
                  isbn13: "9788937473463"
                }
              }
            ],
            numFound: 3,
            resultNum: 3
          }
        }
      };
    }
  },

  // ISBN 기반 도서관 검색 API
  searchLibrariesByISBN: async (isbn, region = '') => {
    const apiKey = process.env.REACT_APP_LIBRARY_API_KEY || 'test_api_key_123';
    
    console.log("🔍 ISBN 기반 도서관 검색 API 호출:", isbn, "지역:", region);
    
    try {
      const params = {
        authKey: apiKey,
        isbn: isbn
      };
      
      // 지역코드가 있으면 추가
      if (region) {
        params.region = region;
      }
      
      const response = await axios.get(`http://data4library.kr/api/libSrchByBook`, {
        params: params,
        timeout: 15000,
        headers: {
          'Accept': 'application/xml, text/xml, */*',
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log("📄 ISBN 기반 도서관 검색 XML 응답:", response.data);
      
      // XML을 JSON으로 파싱
      const result = await parser.parseStringPromise(response.data);
      console.log("🔄 파싱된 JSON:", result);
      
      return {
        data: {
          response: result.response
        }
      };
      
    } catch (error) {
      console.error('ISBN 기반 도서관 검색 API 호출 실패:', error);
      
      // CORS 에러인 경우 프록시 사용
      if (error.code === 'ERR_NETWORK' || error.message.includes('CORS')) {
        console.log("🔄 CORS 에러 - 프록시 사용");
        const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
        const targetUrl = `http://data4library.kr/api/libSrchByBook?authKey=${apiKey}&isbn=${isbn}${region ? `&region=${region}` : ''}`;
        
        try {
          const proxyResponse = await axios.get(proxyUrl + targetUrl, {
            timeout: 15000,
            headers: {
              'Origin': 'http://localhost:3000',
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/xml, text/xml, */*'
            }
          });
          
          console.log("📄 프록시 ISBN 기반 도서관 검색 XML 응답:", proxyResponse.data);
          
          // XML을 JSON으로 파싱
          const proxyResult = await parser.parseStringPromise(proxyResponse.data);
          console.log("🔄 프록시 파싱된 JSON:", proxyResult);
          
          return {
            data: {
              response: proxyResult.response
            }
          };
        } catch (proxyError) {
          console.error('프록시 ISBN 기반 도서관 검색 호출도 실패:', proxyError);
        }
      }
      
      // 에러 시 더미 데이터 반환
      console.log("⚠️ 에러 발생 - 더미 ISBN 기반 도서관 검색 데이터 사용");
      return {
        data: {
          response: {
            libs: {
              lib: [
                {
                  libCode: "111001",
                  libName: "강남구립도서관",
                  address: "서울특별시 강남구 테헤란로 123",
                  tel: "02-1234-5678",
                  homepage: "http://www.gangnamlib.or.kr",
                  operatingTime: "09:00~18:00",
                  closed: "월요일",
                  bookCount: "5"
                },
                {
                  libCode: "111002", 
                  libName: "서초구립도서관",
                  address: "서울특별시 서초구 서초대로 456",
                  tel: "02-2345-6789",
                  homepage: "http://www.seocholib.or.kr",
                  operatingTime: "09:00~18:00",
                  closed: "월요일",
                  bookCount: "3"
                }
              ]
            },
            numFound: "2"
          }
        }
      };
    }
  },

  // 병렬 처리를 통한 대량 도서관 데이터 가져오기
  getLibraryParallel: parallelUtils.measurePerformance('getLibraryParallel', async (startPage = 1, endPage = 10, pageSize = 100, maxConcurrency = 5) => {
    console.log(`🚀 병렬 도서관 데이터 가져오기: ${startPage}~${endPage}페이지 (${pageSize}개씩)`);
    
    const pageNumbers = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);
    
    // 각 페이지별 API 호출 태스크 생성
    const tasks = pageNumbers.map(pageNo => async () => {
      try {
        console.log(`📄 ${pageNo}페이지 데이터 요청 중...`);
        const response = await apiService.getLibrary(pageNo, pageSize);
        console.log(`✅ ${pageNo}페이지 데이터 로드 완료`);
        return { pageNo, data: response, success: true };
      } catch (error) {
        console.error(`❌ ${pageNo}페이지 데이터 로드 실패:`, error);
        return { pageNo, error, success: false };
      }
    });

    // 동시 요청 수 제한하여 병렬 처리
    const results = await parallelUtils.limitConcurrency(tasks, maxConcurrency);
    
    // 성공한 결과만 수집
    const successfulResults = results.filter(result => result.success);
    const failedPages = results.filter(result => !result.success).map(r => r.pageNo);
    
    if (failedPages.length > 0) {
      console.warn(`⚠️ 실패한 페이지: ${failedPages.join(', ')}`);
    }

    // 모든 도서관 데이터 병합
    const allLibraries = successfulResults.flatMap(result => {
      const libraryData = result.data.data.response?.libs || result.data.libs || [];
      return Array.isArray(libraryData) ? libraryData : [libraryData];
    });

    console.log(`🎉 병렬 처리 완료: 총 ${allLibraries.length}개 도서관 데이터 수집`);
    
    return {
      libraries: allLibraries,
      totalPages: successfulResults.length,
      failedPages,
      totalCount: allLibraries.length
    };
  }),

  // 병렬 처리를 통한 ISBN 기반 도서관 검색 (개선된 버전)
  searchLibrariesByISBNParallel: parallelUtils.measurePerformance('searchLibrariesByISBNParallel', async (isbn, regions = [], maxConcurrency = 8) => {
    console.log(`🚀 병렬 ISBN 도서관 검색: ${isbn} (${regions.length}개 지역)`);
    
    // 지역코드와 지역명 매핑
    const regionCodeToName = {
      "11": "서울",
      "21": "부산", 
      "22": "대구",
      "23": "인천",
      "24": "광주",
      "25": "대전",
      "26": "울산",
      "29": "세종",
      "31": "경기",
      "32": "강원",
      "33": "충북",
      "34": "충남",
      "35": "전북",
      "36": "전남",
      "37": "경북",
      "38": "경남",
      "39": "제주"
    };
    
    if (regions.length === 0) {
      // 모든 지역코드 사용
      regions = Object.keys(regionCodeToName);
    }

    // 각 지역별 검색 태스크 생성
    const tasks = regions.map(regionCode => async () => {
      try {
        console.log(`🔍 ${regionCode} 지역 ISBN 검색 시작...`);
        const response = await apiService.searchLibrariesByISBN(isbn, regionCode);
        
        if (response.data?.response?.libs?.lib) {
          const libraries = Array.isArray(response.data.response.libs.lib) 
            ? response.data.response.libs.lib 
            : [response.data.response.libs.lib];
          
          // 각 지역별 상위 3개만 추출
          const top3 = libraries.slice(0, 3);
          
          // 지역명 가져오기
          const regionName = regionCodeToName[regionCode] || regionCode;
          
          // 각 도서관에 지역 정보 추가
          const librariesWithRegion = top3.map(lib => ({
            lib: {
              ...lib,
              region: regionName, // 지역명으로 설정
              regionCode: regionCode, // 지역코드도 보관
              regionName: regionName
            }
          }));
          
          console.log(`✅ ${regionName} 지역: ${top3.length}개 도서관 추출`);
          return { regionCode, regionName, libraries: librariesWithRegion, success: true };
        }
        return { regionCode, regionName: regionCodeToName[regionCode] || regionCode, libraries: [], success: true };
      } catch (error) {
        console.error(`❌ ${regionCode} 지역 검색 실패:`, error);
        return { regionCode, regionName: regionCodeToName[regionCode] || regionCode, error, success: false };
      }
    });

    // 동시 요청 수 제한하여 병렬 처리
    const results = await parallelUtils.limitConcurrency(tasks, maxConcurrency);
    
    // 성공한 결과만 수집
    const successfulResults = results.filter(result => result.success);
    const failedRegions = results.filter(result => !result.success).map(r => r.regionName);
    
    if (failedRegions.length > 0) {
      console.warn(`⚠️ 실패한 지역: ${failedRegions.join(', ')}`);
    }

    // 모든 도서관 데이터 병합
    const allLibraries = successfulResults.flatMap(result => result.libraries);

    console.log(`🎉 병렬 ISBN 검색 완료: 총 ${allLibraries.length}개 도서관 추출`);
    
    return allLibraries;
  }),

  // 병렬 처리를 통한 키워드 검색 (여러 페이지 동시 검색)
  searchBooksByKeywordParallel: parallelUtils.measurePerformance('searchBooksByKeywordParallel', async (keyword, maxPages = 3, pageSize = 20, maxConcurrency = 3) => {
    // 키워드 전처리: 앞의 두 단어만 추출
    const processKeyword = (keyword) => {
      const words = keyword.trim().split(/\s+/).filter(word => word.length > 0);
      return words.slice(0, 2).join(' ');
    };
    
    const processedKeyword = processKeyword(keyword);
    
    console.log(`🚀 병렬 키워드 검색: "${keyword}" (최대 ${maxPages}페이지)`);
    console.log(`📝 전처리된 키워드 (앞 2단어): "${processedKeyword}"`);
    
    const pageNumbers = Array.from({ length: maxPages }, (_, i) => i + 1);
    
    // 각 페이지별 검색 태스크 생성
    const tasks = pageNumbers.map(pageNo => async () => {
      try {
        console.log(`📄 "${processedKeyword}" ${pageNo}페이지 검색 중...`);
        
        // 개선된 키워드 검색 함수 사용
        const response = await apiService.searchBooksByKeyword(keyword, pageNo, pageSize);
        
        if (response.data?.response?.docs?.doc) {
          const books = Array.isArray(response.data.response.docs.doc) 
            ? response.data.response.docs.doc 
            : [response.data.response.docs.doc];
          
          console.log(`✅ "${processedKeyword}" ${pageNo}페이지: ${books.length}개 도서`);
          return { pageNo, books, success: true };
        }
        return { pageNo, books: [], success: true };
      } catch (error) {
        console.error(`❌ "${processedKeyword}" ${pageNo}페이지 검색 실패:`, error);
        return { pageNo, error, success: false };
      }
    });

    // 동시 요청 수 제한하여 병렬 처리
    const results = await parallelUtils.limitConcurrency(tasks, maxConcurrency);
    
    // 성공한 결과만 수집
    const successfulResults = results.filter(result => result.success);
    const failedPages = results.filter(result => !result.success).map(r => r.pageNo);
    
    if (failedPages.length > 0) {
      console.warn(`⚠️ 실패한 페이지: ${failedPages.join(', ')}`);
    }

    // 모든 도서 데이터 병합
    const allBooks = successfulResults.flatMap(result => result.books);

    console.log(`🎉 병렬 키워드 검색 완료: 총 ${allBooks.length}개 도서`);
    console.log(`🔍 사용된 키워드: "${processedKeyword}" (원본: "${keyword}")`);
    
    return {
      books: allBooks,
      totalPages: successfulResults.length,
      failedPages,
      totalCount: allBooks.length,
      processedKeyword: processedKeyword,
      originalKeyword: keyword
    };
  }),

  // 병렬 처리를 통한 제목 검색 (여러 페이지 동시 검색)
  searchBooksByTitleParallel: parallelUtils.measurePerformance('searchBooksByTitleParallel', async (title, maxPages = 3, pageSize = 20, maxConcurrency = 3) => {
    console.log(`🚀 병렬 제목 검색: "${title}" (최대 ${maxPages}페이지)`);
    
    const pageNumbers = Array.from({ length: maxPages }, (_, i) => i + 1);
    
    // 각 페이지별 검색 태스크 생성
    const tasks = pageNumbers.map(pageNo => async () => {
      try {
        console.log(`📄 "${title}" ${pageNo}페이지 검색 중...`);
        const response = await apiService.searchBooksByTitle(title, pageNo, pageSize);
        
        if (response.data?.response?.docs?.doc) {
          const books = Array.isArray(response.data.response.docs.doc) 
            ? response.data.response.docs.doc 
            : [response.data.response.docs.doc];
          
          // 제목 필터링 (더 정확한 매칭)
          const filteredBooks = books.filter(book => {
            const bookTitle = book.bookname?.toLowerCase() || '';
            const searchTitle = title.toLowerCase();
            return bookTitle.includes(searchTitle) || searchTitle.includes(bookTitle);
          });
          
          console.log(`✅ "${title}" ${pageNo}페이지: ${filteredBooks.length}개 도서`);
          return { pageNo, books: filteredBooks, success: true };
        }
        return { pageNo, books: [], success: true };
      } catch (error) {
        console.error(`❌ "${title}" ${pageNo}페이지 검색 실패:`, error);
        return { pageNo, error, success: false };
      }
    });

    // 동시 요청 수 제한하여 병렬 처리
    const results = await parallelUtils.limitConcurrency(tasks, maxConcurrency);
    
    // 성공한 결과만 수집
    const successfulResults = results.filter(result => result.success);
    const failedPages = results.filter(result => !result.success).map(r => r.pageNo);
    
    if (failedPages.length > 0) {
      console.warn(`⚠️ 실패한 페이지: ${failedPages.join(', ')}`);
    }

    // 모든 도서 데이터 병합
    const allBooks = successfulResults.flatMap(result => result.books);

    console.log(`🎉 병렬 제목 검색 완료: 총 ${allBooks.length}개 도서`);
    
    return {
      books: allBooks,
      totalPages: successfulResults.length,
      failedPages,
      totalCount: allBooks.length
    };
  }),

  // 헬스체크 메서드
  healthCheck: healthCheck.checkHealth
};

// 주기적 캐시 정리 (1시간마다)
setInterval(() => {
  cacheUtils.cleanup();
}, CACHE_DURATION);

export default api;
export { healthCheck }; 