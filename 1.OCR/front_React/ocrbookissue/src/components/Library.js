import React, { useState, useEffect, useRef, Suspense } from "react";
import { useLocation } from "react-router-dom";
import { apiService } from "../services/api";
import { lazy } from "react";

const dummyLibraries = [];

// 지역별 색상 매핑
const regionColors = {
  '서울': 'bg-blue-400 text-white',
  '경기': 'bg-green-400 text-white',
  '부산': 'bg-red-400 text-white',
  '대구': 'bg-purple-400 text-white',
  '인천': 'bg-yellow-400 text-gray-900',
  '광주': 'bg-green-600 text-white',
  '대전': 'bg-orange-400 text-white',
  '울산': 'bg-cyan-400 text-gray-900',
  '세종': 'bg-violet-400 text-white',
  '강원': 'bg-indigo-400 text-white',
  '충북': 'bg-yellow-300 text-gray-900',
  '충남': 'bg-orange-300 text-gray-900',
  '전북': 'bg-green-300 text-gray-900',
  '전남': 'bg-blue-300 text-gray-900',
  '경북': 'bg-red-300 text-gray-900',
  '경남': 'bg-green-200 text-gray-900',
  '제주': 'bg-yellow-200 text-gray-900',
  '기타': 'bg-gray-300 text-gray-900',
};

// 지역명 축약형 변환 함수 (개선된 버전)
function getShortRegionName(fullRegion) {
  if (!fullRegion) return '기타';
  
  // 지역코드인 경우 처리
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
  
  // 지역코드인 경우 바로 변환
  if (regionCodeToName[fullRegion]) {
    return regionCodeToName[fullRegion];
  }
  
  // 특별한 경우 먼저 처리 (가장 구체적인 매칭)
  if (fullRegion.includes('충청북') || fullRegion.includes('충북')) return '충북';
  if (fullRegion.includes('충청남') || fullRegion.includes('충남')) return '충남';
  if (fullRegion.includes('전라북') || fullRegion.includes('전북')) return '전북';
  if (fullRegion.includes('전라남') || fullRegion.includes('전남')) return '전남';
  if (fullRegion.includes('경상북') || fullRegion.includes('경북')) return '경북';
  if (fullRegion.includes('경상남') || fullRegion.includes('경남')) return '경남';
  if (fullRegion.includes('강원')) return '강원';
  
  // 정확한 매칭
  const regionMap = {
    '서울': '서울',
    '경기': '경기',
    '부산': '부산',
    '대구': '대구',
    '인천': '인천',
    '광주': '광주',
    '대전': '대전',
    '울산': '울산',
    '세종': '세종',
    '강원': '강원',
    '제주': '제주'
  };
  
  // 정확한 매칭 먼저 시도
  if (regionMap[fullRegion]) {
    return regionMap[fullRegion];
  }
  
  // 앞 5글자로 매칭 (충청, 전라, 경상은 제외)
  const prefix = fullRegion.substring(0, 5);
  for (const [key, value] of Object.entries(regionMap)) {
    if (prefix.includes(key) || key.includes(prefix)) {
      return value;
    }
  }
  
  // 주소에서 지역 추출 시도
  if (fullRegion.includes('특별시') || fullRegion.includes('광역시') || fullRegion.includes('도')) {
    const extractedRegion = fullRegion.split(' ')[0].replace(/특별시|광역시|도/g, '');
    if (regionMap[extractedRegion]) {
      return regionMap[extractedRegion];
    }
  }
  
  return fullRegion;
}

function getRegionColor(region) {
  return regionColors[region] || regionColors['기타'];
}

// 도서관 검색 히스토리 저장 함수
const saveLibraryHistory = (query) => {
  if (!query.trim()) return;
  
  let history = JSON.parse(localStorage.getItem('libraryHistory') || '[]');
  // 이미 동일한 검색어가 있으면 추가하지 않음
  history = history.filter(item => item.query !== query.trim());
  history.unshift({
    id: Date.now() + Math.random().toString(36).slice(2),
    query: query.trim(),
    createdAt: new Date().toISOString()
  });
  localStorage.setItem('libraryHistory', JSON.stringify(history.slice(0, 20)));
};

const LibraryResults = lazy(() => import("./LibraryResults"));

export default function Library() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [libraries, setLibraries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isISBNSearch, setIsISBNSearch] = useState(false);
  const [isbnInfo, setIsbnInfo] = useState(null);
  const [displayLibraries, setDisplayLibraries] = useState([]);
  const location = useLocation();
  const containerRef = useRef(null);

  // 페이지당 아이템 수
  const ITEMS_PER_PAGE = 20;

  // 페이지 진입 시 상태 초기화 및 로딩 상태 설정
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const bookParam = params.get("book");
    const searchTypeParam = params.get("searchType");
    const queryParam = params.get("query");
    const skipLoading = localStorage.getItem('skipLoading') === 'true';
    
    // 히스토리에서 온 경우 skipLoading 플래그 제거
    if (skipLoading) {
      localStorage.removeItem('skipLoading');
    }
    
    // URL 파라미터가 없으면 검색 관련 상태 초기화
    if (!bookParam && !searchTypeParam && !queryParam) {
      setQuery("");
      setSearch("");
      setIsISBNSearch(false);
      setIsbnInfo(null);
      setCurrentPage(1);
      setHasMore(true);
      setError("");
      setLoading(false); // 초기화 완료 후 로딩 상태 해제
    } else {
      // URL 파라미터가 있으면 로딩 상태 설정 (히스토리에서 온 경우 제외)
      if (!skipLoading) {
        setLoading(true);
      }
    }
  }, [location.pathname]); // pathname이 변경될 때만 실행

  // 검색 결과 필터링 (캐싱된 데이터에서 검색)
  const filtered = libraries.filter(lib => {
    // ISBN 검색 결과의 경우 lib 객체 안에 있는 데이터 구조
    const displayLib = lib.lib || lib;
    
    const region = displayLib.region || displayLib.regionName || (displayLib.address ? displayLib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
    const shortRegion = getShortRegionName(region);
    
    const searchFields = [
      displayLib.libName,
      displayLib.libCode,
      displayLib.address,
      displayLib.tel,
      displayLib.phone,
      displayLib.homepage,
      region,
      shortRegion
    ];
    
    const searchTerm = search.toLowerCase();
    return searchFields.some(field => 
      field && field.toString().toLowerCase().includes(searchTerm)
    );
  });

  // 페이지 변경 시 도서관 목록 업데이트
  useEffect(() => {
    if (libraries.length > 0) {
      if (search.trim()) {
        // 검색어가 있는 경우: 필터링된 결과를 페이지별로 표시
        const startIndex = 0;
        const endIndex = currentPage * ITEMS_PER_PAGE;
        const currentSearchResults = filtered.slice(startIndex, endIndex);
        setDisplayLibraries(currentSearchResults);
        setHasMore(currentSearchResults.length < filtered.length);
      } else {
        // 검색어가 없는 경우: 캐싱된 도서관 목록을 페이지별로 표시
        const startIndex = 0;
        const endIndex = currentPage * ITEMS_PER_PAGE;
        const currentLibraries = libraries.slice(startIndex, endIndex);
        setDisplayLibraries(currentLibraries);
        setHasMore(endIndex < libraries.length);
      }
    }
  }, [currentPage, libraries, search]);

  // 더 보기 버튼 클릭
  const loadMore = async () => {
    const currentTotal = currentPage * ITEMS_PER_PAGE;
    const remainingCached = libraries.length - currentTotal;
    
    if (remainingCached >= ITEMS_PER_PAGE) {
      // 캐싱된 데이터가 충분한 경우
      setCurrentPage(prev => prev + 1);
    } else {
      // 캐싱된 데이터가 부족한 경우 API 호출
      await loadMoreFromAPI();
    }
  };

  // API에서 추가 데이터 로드
  const loadMoreFromAPI = async () => {
    try {
      setLoading(true);
      
      // 현재 캐싱된 데이터의 페이지 수 추정
      const estimatedCurrentPages = Math.ceil(libraries.length / 100);
      const nextPage = estimatedCurrentPages + 1;
      
      const response = await apiService.getLibrary(nextPage, 100);
      const newLibraries = response.data.response?.libs || response.data.libs || [];
      
      if (newLibraries.length > 0) {
        // 새로운 데이터를 캐싱에 추가
        const updatedLibraries = [...libraries, ...newLibraries];
        setLibraries(updatedLibraries);
        
        // 페이지 업데이트
        setCurrentPage(prev => prev + 1);
        setHasMore(newLibraries.length === 100); // 100개씩 가져오므로 100개면 더 있을 가능성
      } else {
        // 더 이상 데이터가 없으면 버튼 숨기기
        setHasMore(false);
      }
      
    } catch (error) {
      // API 호출 실패 시 버튼 숨기기
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  // 최상단 이동 함수
  const scrollToTop = () => {
    // 실제 스크롤 컨테이너 찾기
    const scrollContainer = document.querySelector('div[class="flex-1 overflow-y-auto"]');
    if (scrollContainer) {
      try {
        scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (e) {
        scrollContainer.scrollTop = 0;
      }
    } else {
      // fallback으로 window 스크롤 시도
      window.scrollTo(0, 0);
      setTimeout(() => {
        try {
          window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
        } catch (e) {
        }
      }, 100);
    }
  };

  // 스크롤 이벤트 리스너 추가
  useEffect(() => {
    const handleScroll = () => {
      // 스크롤 위치에 따른 추가 로직이 필요하면 여기에 추가
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 도서관 데이터 가져오기 (병렬 처리 적용)
  const fetchLibraries = async (pageNo = 1, searchQuery = "") => {
    try {
      setLoading(true);
      setError("");
      
      if (pageNo === 1) {
        // 첫 페이지 로드 시 병렬 처리로 여러 페이지를 동시에 가져오기
        const parallelResponse = await apiService.getLibraryParallel(1, 5, 100, 3);
        
        if (parallelResponse.libraries && parallelResponse.libraries.length > 0) {
          setLibraries(parallelResponse.libraries);
          setHasMore(parallelResponse.totalPages >= 5);
          setCurrentPage(5);
        } else {
          // 병렬 처리 실패 시 기존 방식으로 폴백
          const response = await apiService.getLibrary(pageNo, 100);
          const libraryData = response.data.response?.libs || response.data.libs || [];
          setLibraries(libraryData);
          setHasMore(true);
          setCurrentPage(pageNo);
        }
      } else {
        // 추가 페이지 로드 시 기존 방식 사용
        const response = await apiService.getLibrary(pageNo, 100);
        const libraryData = response.data.response?.libs || response.data.libs || [];
        setLibraries(prev => [...prev, ...libraryData]);
        setHasMore(libraryData.length === 100);
        setCurrentPage(pageNo);
      }
      
    } catch (error) {
      setError("도서관 정보를 가져오는데 실패했습니다. 더미 데이터를 사용합니다.");
      
      // 에러 시 더미 데이터 사용
      setLibraries(dummyLibraries);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    // URL 파라미터가 없고 ISBN 검색이 아닌 경우에만 기본 도서관 데이터 로드
    const params = new URLSearchParams(location.search);
    const hasBookParam = params.get("book");
    
    if (!hasBookParam && !isISBNSearch) {
      fetchLibraries(1, "");
    }
  }, []);

  // URL 파라미터에서 책 정보 가져오기
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const bookParam = params.get("book");
    const isbnParam = params.get("isbn");
    const searchTypeParam = params.get("searchType");
    const librariesParam = params.get("libraries");
    const totalCountParam = params.get("totalCount");
    const regionParam = params.get("region");
    const regionNameParam = params.get("regionName");
    const queryParam = params.get("query"); // 도서관 검색 히스토리에서 넘어온 검색어
    
    // 도서관 검색 히스토리에서 넘어온 검색어 처리
    if (queryParam) {
      setQuery(queryParam);
      setSearch(queryParam);
      setCurrentPage(1);
      // 검색 실행
      const filtered = libraries.filter(lib => {
        const displayLib = lib.lib || lib;
        const region = displayLib.region || displayLib.regionName || (displayLib.address ? displayLib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
        const shortRegion = getShortRegionName(region);
        
        const searchFields = [
          displayLib.libName,
          displayLib.libCode,
          displayLib.address,
          displayLib.tel,
          displayLib.phone,
          displayLib.homepage,
          region,
          shortRegion
        ];
        
        const searchTerm = queryParam.toLowerCase();
        return searchFields.some(field => 
          field && field.toString().toLowerCase().includes(searchTerm)
        );
      });
      
      if (filtered.length > 0) {
        setDisplayLibraries(filtered.slice(0, ITEMS_PER_PAGE));
        setHasMore(filtered.length > ITEMS_PER_PAGE);
      }
      return; // 다른 파라미터 처리 중단
    }
    
    if (bookParam) {
      setQuery(bookParam);
      // ISBN 검색인 경우 검색어를 초기화하여 필터링 방지
      if (searchTypeParam === 'isbn' || searchTypeParam === 'all' || searchTypeParam === 'single') {
        setSearch("");
      } else {
        setSearch(bookParam);
        // 일반 검색 시 ISBN 검색 상태 초기화
        setIsISBNSearch(false);
        setIsbnInfo(null);
      }
    }
    
    // ISBN 기반 도서관 검색 결과가 있으면 처리
    if ((searchTypeParam === 'isbn' || searchTypeParam === 'all' || searchTypeParam === 'single') && librariesParam) {
      try {
        const isbnLibraries = JSON.parse(librariesParam);
        // ISBN 검색 상태 설정
        setIsISBNSearch(true);
        setIsbnInfo({
          isbn: isbnParam,
          bookTitle: bookParam,
          totalCount: totalCountParam,
          region: regionParam,
          regionName: regionNameParam,
          searchType: searchTypeParam
        });
        
        // 도서관 데이터 구조 변환
        const processedLibraries = isbnLibraries.map(item => {
          const lib = item.lib || item;
          return {
            libCode: lib.libCode,
            libName: lib.libName,
            address: lib.address,
            tel: lib.tel,
            homepage: lib.homepage,
            operatingTime: lib.operatingTime,
            closed: lib.closed,
            bookCount: lib.bookCount,
            region: lib.region || (lib.address ? lib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타'),
            regionName: lib.regionName
          };
        });
        
        setLibraries(processedLibraries);
        setHasMore(false); // ISBN 검색 결과는 한 번에 모든 결과를 가져옴
        
      } catch (error) {
        // 파싱 실패 시 기존 방식으로 도서관 데이터 로드
        setIsISBNSearch(false);
        setIsbnInfo(null);
        fetchLibraries(1, bookParam);
      }
    } else if (bookParam && searchTypeParam !== 'isbn' && searchTypeParam !== 'all' && searchTypeParam !== 'single') {
      // 일반 검색인 경우에만 기존 방식으로 도서관 데이터 로드
      setIsISBNSearch(false);
      setIsbnInfo(null);
      fetchLibraries(1, bookParam);
    }
  }, [location.search]);

  // 통합 검색: 도서관명, 주소, 전화번호, 지역명으로 검색
  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setSearch(query);
      setCurrentPage(1); // 검색 시 페이지 리셋
      saveLibraryHistory(query); // 히스토리에 저장
    }
  };

  // 캐싱된 도서관 목록을 20개씩 보여주기
  const showCachedLibraryList = () => {
    const startIndex = 0;
    const endIndex = currentPage * ITEMS_PER_PAGE;
    const currentLibraries = libraries.slice(startIndex, endIndex);
    
    setDisplayLibraries(currentLibraries);
    setHasMore(endIndex < libraries.length);
  };

  // 추가 데이터를 가져와서 캐싱 데이터에 추가
  const fetchAdditionalDataAndAddToCache = async (searchQuery) => {
    try {
      setLoading(true);
      setError("");
      
      // 현재 캐싱된 데이터의 페이지 수 추정
      const estimatedCurrentPages = Math.ceil(libraries.length / 100);
      const startPage = estimatedCurrentPages + 1;
      const endPage = startPage + 4; // 5페이지 추가로 가져오기
      
      // 병렬 처리로 여러 페이지를 동시에 가져오기
      const parallelResponse = await apiService.getLibraryParallel(startPage, endPage, 100, 5);
      
      if (parallelResponse.libraries && parallelResponse.libraries.length > 0) {
        // 새로운 데이터를 기존 캐싱 데이터에 추가
        const updatedLibraries = [...libraries, ...parallelResponse.libraries];
        setLibraries(updatedLibraries);
        
        // 검색 결과가 있으면 에러 메시지 클리어
        setError("");
      } else {
        setError("추가 데이터를 가져올 수 없습니다.");
      }
      
    } catch (error) {
      setError("추가 데이터를 가져오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 캐시 비우기 및 새로고침
  const clearCacheAndRefresh = async () => {
    try {
      setLoading(true);
      setError("");
      
      // API 서비스의 캐시 비우기
      apiService.clearCache();
      
      // 새로운 데이터 가져오기
      await fetchLibraries(1, search);
      
    } catch (error) {
      console.error("❌ 캐시 비우기 실패:", error);
      setError("캐시 비우기에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // ISBN 검색 결과 클리어
  const clearISBNResults = () => {
    setLibraries([]);
    setIsISBNSearch(false);
    setCurrentPage(1);
    setHasMore(true);
    // 기본 도서관 데이터 다시 로드
    fetchLibraries(1, search);
  };

  // 서버에서 더 많은 데이터 검색 (병렬 처리 적용)
  const searchMoreFromServer = async () => {
    try {
      setLoading(true);
      
      // 현재 캐싱된 데이터의 페이지 수 추정 (100개씩 로드한다고 가정)
      const estimatedCurrentPages = Math.ceil(libraries.length / 100);
      const startPage = estimatedCurrentPages + 1; // 추정된 페이지 다음부터 시작
      const endPage = startPage + 9; // 최대 10페이지까지 병렬 검색
      
      // 병렬 처리로 여러 페이지를 동시에 검색
      const parallelResponse = await apiService.getLibraryParallel(startPage, endPage, 100, 5);
      
      if (parallelResponse.libraries && parallelResponse.libraries.length > 0) {
        // 검색어로 필터링
        const filteredData = parallelResponse.libraries.filter(lib => {
          const region = lib.region || (lib.address ? lib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
          const shortRegion = getShortRegionName(region);
          
          const searchFields = [
            lib.libName,
            lib.libCode,
            lib.address,
            lib.tel,
            lib.homepage,
            region,
            shortRegion
          ];
          
          const searchTerm = search.toLowerCase();
          return searchFields.some(field => 
            field && field.toString().toLowerCase().includes(searchTerm)
          );
        });
        
        if (filteredData.length > 0) {
          setLibraries(prev => [...prev, ...filteredData]);
          setError(""); // 에러 메시지 클리어
        } else {
          setError("더 많은 페이지를 검색했지만 결과를 찾을 수 없습니다.");
        }
      } else {
        setError("서버에서 추가 데이터를 가져올 수 없습니다.");
      }
      
    } catch (error) {
      console.error("❌ 병렬 검색 중 오류:", error);
      setError("서버 검색 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={containerRef} className="flex flex-col items-center w-full min-h-screen flex-1 p-2 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {/* 통합 검색창 */}
      <form className="w-full max-w-xs mb-2 flex gap-2" onSubmit={handleSearch}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="도서관명, 주소, 전화번호, 지역명으로 검색"
          className="w-full rounded px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow"
        />
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded font-bold hover:bg-blue-700 transition text-lg">🔍</button>
      </form>

      {/* 로딩 상태 */}
      {loading && (
        <div className="w-full max-w-xs text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">도서관 정보를 불러오는 중...</span>
        </div>
      )}

      {/* 에러 메시지 */}
      {error && (
        <div className="w-full max-w-xs text-center py-2 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* 검색 결과 헤더 */}
      {search && !isISBNSearch ? (
        <div className="w-full max-w-xs bg-green-50 dark:bg-green-900 rounded-lg p-3 mb-3 text-center">
          <div className="text-lg font-bold text-green-700 dark:text-green-300 mb-1">
            🔍 도서관 검색 결과
          </div>
          <div className="text-sm text-green-600 dark:text-green-400 mb-1">
            검색어: {search}
          </div>
          <div className="text-xs text-green-500 dark:text-green-400">
            {libraries.length > 0 ? `총 ${libraries.length}개 중 ${displayLibraries.length}개 로드됨` : '전체 데이터에서 검색 중'}
          </div>
        </div>
      ) : !search && !isISBNSearch && libraries.length > 0 ? (
        <div className="w-full max-w-xs bg-blue-50 dark:bg-blue-900 rounded-lg p-3 mb-3 text-center">
          <div className="text-lg font-bold text-blue-700 dark:text-blue-300 mb-1">
            📚 도서관 목록
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
            캐싱된 도서관 데이터
          </div>
          <div className="text-xs text-blue-500 dark:text-blue-400">
            총 {libraries.length}개 중 {displayLibraries.length}개 표시
          </div>
        </div>
      ) : null}

      {/* ISBN 기반 검색 결과 헤더 */}
      {isISBNSearch && isbnInfo && (
        <div className="w-full max-w-xs bg-blue-50 dark:bg-blue-900 rounded-lg p-3 mb-3 text-center">
          <div className="text-lg font-bold text-blue-700 dark:text-blue-300 mb-1">
            📚 ISBN 기반 도서관 검색
            {isbnInfo.searchType === 'all' && <span className="text-sm"> (전체 지역)</span>}
          </div>
          <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
            도서: {isbnInfo.bookTitle}
          </div>
          <div className="text-xs text-blue-500 dark:text-blue-400 mb-1">
            ISBN: {isbnInfo.isbn} | 총 {isbnInfo.totalCount || libraries.length}개 도서관
          </div>
          {isbnInfo.regionName && isbnInfo.searchType === 'single' && (
            <div className="text-xs text-blue-500 dark:text-blue-400">
              지역: {isbnInfo.regionName} ({isbnInfo.region})
            </div>
          )}
          {isbnInfo.searchType === 'all' && (
            <div className="text-xs text-blue-500 dark:text-blue-400">
              🌍 전국 17개 지역 검색 완료
            </div>
          )}
        </div>
      )}

      {/* 도서관 검색 결과 표시 부분을 lazy 컴포넌트로 대체 */}
      <Suspense fallback={<div className="w-full max-w-md mx-auto text-center py-8"><div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div><div className="text-gray-600 dark:text-gray-400">도서관 정보를 불러오는 중...</div></div>}>
        <LibraryResults
          libraries={libraries}
          displayLibraries={displayLibraries}
          loading={loading}
          error={error}
          isISBNSearch={isISBNSearch}
          isbnInfo={isbnInfo}
          searchQuery={search}
          totalCount={libraries.length}
          hasMore={hasMore}
          onLoadMore={loadMoreFromAPI}
          onClearISBNResults={clearISBNResults}
          onShowCachedList={showCachedLibraryList}
          onClearCacheAndRefresh={clearCacheAndRefresh}
        />
      </Suspense>

      {/* 더 보기 버튼 */}
      {!loading && hasMore && displayLibraries.length > 0 && (
        <button 
          onClick={loadMore}
          className="w-full max-w-xs mt-4 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border border-violet-400"
        >
          {search.trim() ? 
            `📚 더 많은 검색 결과 로드 (${ITEMS_PER_PAGE}건 더)` : 
            `📚 더 많은 도서관 로드 (${ITEMS_PER_PAGE}건 더)`
          }
        </button>
      )}

      {/* 최상단 이동 플로팅 버튼 */}
      {displayLibraries.length > 20 && (
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            scrollToTop();
          }}
          className="fixed bottom-24 right-4 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-xl hover:shadow-2xl transform hover:scale-110 transition-all duration-200 z-[9999] flex items-center justify-center md:bottom-6 md:right-6 cursor-pointer border-2 border-white"
          title="최상단으로 이동"
          type="button"
        >
          <span className="text-xl font-bold">↑</span>
        </button>
      )}
    </div>
  );
} 