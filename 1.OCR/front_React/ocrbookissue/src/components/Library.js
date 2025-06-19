import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { apiService } from "../services/api";

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

export default function Library() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [libraries, setLibraries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isISBNSearch, setIsISBNSearch] = useState(false);
  const [isbnInfo, setIsbnInfo] = useState(null);
  const [displayPage, setDisplayPage] = useState(1);
  const [displayLibraries, setDisplayLibraries] = useState([]);
  const location = useLocation();
  const containerRef = useRef(null);

  // 페이지당 아이템 수
  const ITEMS_PER_PAGE = 20;

  // 페이지 변경 시 도서관 목록 업데이트
  useEffect(() => {
    if (libraries.length > 0) {
      const startIndex = 0;
      const endIndex = displayPage * ITEMS_PER_PAGE;
      const currentLibraries = libraries.slice(startIndex, endIndex);
      setDisplayLibraries(currentLibraries);
      setHasMore(endIndex < libraries.length);
      
      // 플로팅 버튼 디버깅
      console.log(`📊 도서관 데이터 상태: 전체 ${libraries.length}개, 표시 ${currentLibraries.length}개, 플로팅 버튼 표시: ${currentLibraries.length > 20}`);
    }
  }, [displayPage, libraries]);

  // 더 보기 버튼 클릭
  const loadMore = () => {
    setDisplayPage(prev => prev + 1);
  };

  // 최상단 이동 함수
  const scrollToTop = () => {
    console.log("🔝 최상단 이동 버튼 클릭됨");
    
    // 실제 스크롤 컨테이너 찾기
    const scrollContainer = document.querySelector('div[class="flex-1 overflow-y-auto"]');
    if (scrollContainer) {
      try {
        scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
        console.log("✅ 실제 스크롤 컨테이너 스크롤 실행됨");
      } catch (e) {
        scrollContainer.scrollTop = 0;
        console.log("⚠️ scrollContainer.scrollTop fallback");
      }
    } else {
      console.log("❌ 스크롤 컨테이너를 찾을 수 없음");
      // fallback으로 window 스크롤 시도
      window.scrollTo(0, 0);
      setTimeout(() => {
        try {
          window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
          console.log("✅ window.scrollTo fallback 실행됨");
        } catch (e) {
          console.log("⚠️ window.scrollTo fallback 실패");
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
      
      console.log("🔍 도서관 데이터 가져오기 시작...");
      
      if (pageNo === 1) {
        // 첫 페이지 로드 시 병렬 처리로 여러 페이지를 동시에 가져오기
        console.log("🚀 병렬 처리로 대량 데이터 로드 시작...");
        const parallelResponse = await apiService.getLibraryParallel(1, 5, 100, 3);
        
        console.log("📊 병렬 처리 결과:", parallelResponse);
        
        if (parallelResponse.libraries && parallelResponse.libraries.length > 0) {
          setLibraries(parallelResponse.libraries);
          setHasMore(parallelResponse.totalPages >= 5);
          setCurrentPage(5);
          console.log(`✅ 병렬 처리 완료: ${parallelResponse.libraries.length}개 도서관 데이터 로드`);
        } else {
          // 병렬 처리 실패 시 기존 방식으로 폴백
          console.log("⚠️ 병렬 처리 실패 - 기존 방식으로 폴백");
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
      console.error("❌ 도서관 데이터 가져오기 에러:", error);
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
        console.log("📚 ISBN 기반 도서관 검색 결과 파싱:", isbnLibraries);
        console.log("📚 검색 타입:", searchTypeParam);
        console.log("📚 도서관 개수:", isbnLibraries.length);
        
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
          console.log("📚 개별 도서관 데이터:", lib);
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
        
        console.log("📚 처리된 도서관 데이터:", processedLibraries);
        console.log("📚 처리된 도서관 개수:", processedLibraries.length);
        
        setLibraries(processedLibraries);
        setHasMore(false); // ISBN 검색 결과는 한 번에 모든 결과를 가져옴
        
        console.log("✅ ISBN 기반 도서관 검색 결과 설정 완료:", processedLibraries.length, "개");
        
      } catch (error) {
        console.error("❌ ISBN 기반 도서관 검색 결과 파싱 실패:", error);
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
    setSearch(query);
    setDisplayPage(1); // 페이지 리셋
  };

  // 검색 결과 필터링 (캐싱된 데이터에서 검색)
  const filtered = displayLibraries.filter(lib => {
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

  console.log("🔍 현재 검색어:", search);
  console.log("🔍 전체 도서관 개수:", libraries.length);
  console.log("🔍 필터링된 도서관 개수:", filtered.length);
  console.log("🔍 필터링된 도서관:", filtered);

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
      console.log("🔍 서버에서 병렬 검색 시작:", search);
      
      // 현재 캐싱된 데이터의 페이지 수 추정 (100개씩 로드한다고 가정)
      const estimatedCurrentPages = Math.ceil(libraries.length / 100);
      const startPage = estimatedCurrentPages + 1; // 추정된 페이지 다음부터 시작
      const endPage = startPage + 9; // 최대 10페이지까지 병렬 검색
      
      console.log(`🔍 현재 캐싱된 데이터: ${libraries.length}개 (추정 ${estimatedCurrentPages}페이지)`);
      console.log(`🔍 ${startPage}~${endPage}페이지 병렬 검색 시작`);
      
      // 병렬 처리로 여러 페이지를 동시에 검색
      const parallelResponse = await apiService.getLibraryParallel(startPage, endPage, 100, 5);
      
      console.log("📊 병렬 검색 결과:", parallelResponse);
      
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
          console.log(`✅ 병렬 검색으로 ${filteredData.length}개 결과 발견`);
          setLibraries(prev => [...prev, ...filteredData]);
          setError(""); // 에러 메시지 클리어
        } else {
          console.log(`❌ 병렬 검색 완료했지만 결과를 찾을 수 없음`);
          setError("더 많은 페이지를 검색했지만 결과를 찾을 수 없습니다.");
        }
      } else {
        console.log(`❌ 병렬 검색 실패 또는 데이터 없음`);
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
      {search && !isISBNSearch && (
        <div className="w-full max-w-xs bg-green-50 dark:bg-green-900 rounded-lg p-3 mb-3 text-center">
          <div className="text-lg font-bold text-green-700 dark:text-green-300 mb-1">
            🔍 도서관 검색 결과
          </div>
          <div className="text-sm text-green-600 dark:text-green-400 mb-1">
            검색어: {search}
          </div>
          <div className="text-xs text-green-500 dark:text-green-400">
            {libraries.length > 0 ? `총 ${libraries.length}개 중 ${filtered.length}개 로드됨` : '전체 데이터에서 검색 중'}
          </div>
        </div>
      )}

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

      {/* 도서관 결과 리스트 */}
      <div className="w-full max-w-xs rounded-xl shadow-inner p-3 mt-2">
        {!loading && filtered.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="mb-4">검색 결과가 없습니다.</div>
            {search && (
              <div className="space-y-2">
                <div className="text-xs text-gray-400 mb-2">
                  현재 {libraries.length}개 도서관 데이터에서 검색됨
                </div>
                <button 
                  onClick={() => {
                    console.log("🔍 서버에서 추가 데이터 검색:", search);
                    searchMoreFromServer();
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded font-bold hover:bg-blue-700 transition"
                >
                  🚀 병렬 검색 (10페이지 동시)
                </button>
              </div>
            )}
          </div>
        ) : (
          <ul className="flex flex-col gap-4">
            {filtered.map((lib, idx) => {
              // 지역명 추출 (API/더미 데이터 모두 region 또는 address에서 추출)
              let region = '기타';
              let shortRegion = '기타';
              
              // ISBN 검색 결과의 경우 lib 객체 안에 있는 데이터 구조
              if (lib.lib) {
                region = lib.lib.region || lib.lib.regionName || (lib.lib.address ? lib.lib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
                shortRegion = getShortRegionName(region);
              } else {
                // 일반 도서관 데이터의 경우
                region = lib.region || lib.regionName || (lib.address ? lib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
                shortRegion = getShortRegionName(region);
              }
              
              // 실제 표시할 도서관 데이터
              const displayLib = lib.lib || lib;
              
              return (
                <li key={idx} className="bg-white dark:bg-gray-900 rounded-lg shadow p-4 flex flex-col gap-1 relative">
                  <div className="flex items-start justify-between">
                    <div className="text-lg font-bold text-violet-700 dark:text-violet-300 break-words flex-1 min-w-0 mr-2">
                      {displayLib.libName || displayLib.name}
                    </div>
                    <span className={`ml-2 px-2 py-1 rounded text-xs font-bold ${getRegionColor(shortRegion)} whitespace-nowrap flex-shrink-0`}>{shortRegion}</span>
                  </div>
                  <div className="text-xs text-gray-700 dark:text-gray-300">주소: {displayLib.address || '주소 정보 없음'}</div>
                  <div className="text-xs text-gray-700 dark:text-gray-300">운영시간: {displayLib.operatingTime || displayLib.hours || '운영시간 정보 없음'}</div>
                  <div className="text-xs text-gray-700 dark:text-gray-300">전화번호: {displayLib.tel || displayLib.phone || '전화번호 정보 없음'}</div>
                  <div className="text-xs text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <span className="whitespace-nowrap">홈페이지:</span>
                    <div className="flex items-center gap-1 flex-1 min-w-0">
                      <a href={displayLib.homepage} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-300 no-underline font-bold truncate flex-1 min-w-0">
                        {displayLib.homepage || '홈페이지 정보 없음'}
                      </a>
                      <span className="flex-shrink-0 text-blue-500 dark:text-blue-400 text-sm">🔗</span>
                    </div>
                  </div>
                  {displayLib.BookCount && (
                    <div className="text-sm text-emerald-600 dark:text-emerald-400 font-semibold">📚 도서 수: {displayLib.BookCount}권</div>
                  )}
                  {displayLib.bookCount && (
                    <div className="text-sm text-emerald-600 dark:text-emerald-400 font-semibold">📚 도서 수: {displayLib.bookCount}권</div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* 더 보기 버튼 */}
      {!loading && hasMore && filtered.length > 0 && (
        <button 
          onClick={loadMore}
          className="w-full max-w-xs mt-4 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border border-violet-400"
        >
          📚 더 많은 도서관 로드 (20건 더)
        </button>
      )}

      {/* 최상단 이동 플로팅 버튼 */}
      {displayLibraries.length > 20 && (
        <button
          onClick={(e) => {
            console.log("🔘 플로팅 버튼 클릭 이벤트 발생");
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