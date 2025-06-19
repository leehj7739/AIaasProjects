import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { apiService } from "../services/api";
import FallbackImage from "./FallbackImage";

const dummyBooks = [
  { title: "위버멘쉬", author: "프리드리히 니체", desc: "누구의 시선도 아닌, 내 의지대로 살겠다는 선언", img: "https://image.aladin.co.kr/product/32425/0/cover500/k112939963_1.jpg", isbn: "9788960861234" },
  { title: "데미안", author: "헤르만 헤세", desc: "자아를 찾아가는 성장의 여정", img: "https://image.aladin.co.kr/product/32425/0/cover500/8937460446_1.jpg", isbn: "9788937473456" },
  { title: "호밀밭의 파수꾼", author: "J.D. 샐린저", desc: "청춘의 방황과 진실에 대한 갈망", img: "https://image.aladin.co.kr/product/32425/0/cover500/8937460447_1.jpg", isbn: "9788937473463" },
  { title: "1984", author: "조지 오웰", desc: "감시와 통제, 자유에 대한 경고", img: "https://image.aladin.co.kr/product/32425/0/cover500/8982739394_1.jpg", isbn: "9788937473470" }
];

// ISBN 정규식 검증 함수
const isValidISBN = (input) => {
  // ISBN-13 형식: 978-0-7475-3269-9 또는 9780747532699
  const isbn13Regex = /^(?:978|979)-?\d{1,5}-?\d{1,7}-?\d{1,6}-?\d{1}$/;
  // ISBN-10 형식: 0-7475-3269-9 또는 0747532699
  const isbn10Regex = /^\d{1,5}-?\d{1,7}-?\d{1,6}-?\d{1}$/;
  
  const cleanInput = input.replace(/[-\s]/g, '');
  
  return isbn13Regex.test(input) || isbn10Regex.test(input) || 
         (cleanInput.length === 13 && /^978|979/.test(cleanInput)) ||
         (cleanInput.length === 10 && /^\d{10}$/.test(cleanInput));
};

// ISBN 정규화 함수 (하이픈 제거)
const normalizeISBN = (isbn) => {
  return isbn.replace(/[-\s]/g, '');
};

// 지역코드 옵션 (상수)
const regionOptions = [
  { code: "11", name: "서울" },
  { code: "21", name: "부산" },
  { code: "22", name: "대구" },
  { code: "23", name: "인천" },
  { code: "24", name: "광주" },
  { code: "25", name: "대전" },
  { code: "26", name: "울산" },
  { code: "29", name: "세종" },
  { code: "31", name: "경기" },
  { code: "32", name: "강원" },
  { code: "33", name: "충북" },
  { code: "34", name: "충남" },
  { code: "35", name: "전북" },
  { code: "36", name: "전남" },
  { code: "37", name: "경북" },
  { code: "38", name: "경남" },
  { code: "39", name: "제주" }
];

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

export default function Info({ searchQuery, setSearchQuery }) {
  const [search, setSearch] = useState("");
  const [result, setResult] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState(""); // "isbn" 또는 "keyword"
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [allSearchResults, setAllSearchResults] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  // 페이지당 아이템 수
  const ITEMS_PER_PAGE = 20;

  // 페이지 변경 시 검색 결과 업데이트
  useEffect(() => {
    if (allSearchResults.length > 0) {
      const startIndex = 0;
      const endIndex = currentPage * ITEMS_PER_PAGE;
      const currentResults = allSearchResults.slice(startIndex, endIndex);
      setSearchResults(currentResults);
      setHasMore(endIndex < allSearchResults.length);
    }
  }, [currentPage, allSearchResults]);

  // 더 보기 버튼 클릭
  const loadMore = () => {
    setCurrentPage(prev => prev + 1);
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryParam = params.get("query");
    if (queryParam) {
      setSearchQuery(queryParam);
      setSearch(queryParam);
      setSearched(true);
      performSearch(queryParam);
    }
  }, [location.search, setSearchQuery]);

  const performSearch = async (searchTerm) => {
    if (!searchTerm.trim()) {
      setResult(null);
      setSearchResults([]);
      setSearched(false);
      setSearchType("");
      return;
    }

    setLoading(true);
    setSearched(true);

    try {
      if (isValidISBN(searchTerm)) {
        // ISBN 검색
        console.log("🔍 ISBN 검색 실행:", searchTerm);
        setSearchType("isbn");
        const response = await apiService.getBookByISBN(normalizeISBN(searchTerm));
        
        console.log("📄 ISBN 검색 응답 전체:", response);
        console.log("📄 ISBN 검색 응답 데이터:", response.data);
        console.log("📄 ISBN 검색 응답 구조:", response.data?.response);
        
        // 다양한 응답 구조 시도
        let bookData = null;
        let loanInfo = null;
        
        // 구조 1: detail[0].book
        if (response.data?.response?.detail?.[0]?.book) {
          bookData = response.data.response.detail[0].book;
          loanInfo = response.data.response.loanInfo;
          console.log("✅ 구조 1로 데이터 추출 성공");
        }
        // 구조 2: detail.book (배열이 아닌 경우)
        else if (response.data?.response?.detail?.book) {
          bookData = response.data.response.detail.book;
          loanInfo = response.data.response.loanInfo;
          console.log("✅ 구조 2로 데이터 추출 성공");
        }
        // 구조 3: 직접 book 객체
        else if (response.data?.response?.book) {
          bookData = response.data.response.book;
          loanInfo = response.data.response.loanInfo;
          console.log("✅ 구조 3으로 데이터 추출 성공");
        }
        // 구조 4: 다른 가능한 구조들
        else if (response.data?.response?.docs?.doc) {
          const doc = Array.isArray(response.data.response.docs.doc) 
            ? response.data.response.docs.doc[0] 
            : response.data.response.docs.doc;
          bookData = doc;
          console.log("✅ 구조 4로 데이터 추출 성공");
        }
        
        console.log("📚 추출된 도서 데이터:", bookData);
        console.log("📊 추출된 대출 정보:", loanInfo);
        
        if (bookData) {
          // bookImageURL, img에 /book_image.jpg가 들어오면 /dummy-image.png로 대체
          let imgUrl = bookData.bookImageURL || bookData.img || "";
          if (imgUrl.includes("/book_image.jpg")) imgUrl = "/dummy-image.png";
          const resultData = {
            title: bookData.bookname || bookData.title,
            author: bookData.authors || bookData.author,
            publisher: bookData.publisher,
            publication_year: bookData.publication_year,
            desc: bookData.description || bookData.desc,
            img: imgUrl || "/dummy-image.png",
            isbn: bookData.isbn13 || bookData.isbn || searchTerm,
            loanInfo: loanInfo
          };
          
          setResult(resultData);
          setSearchResults([]);
        } else {
          console.log("❌ 도서 데이터를 찾을 수 없습니다.");
          setResult(null);
          setSearchResults([]);
        }
      } else {
        // 제목 검색 (병렬 처리 적용)
        console.log("🔍 제목 검색 실행:", searchTerm);
        setSearchType("title");
        
        // 병렬 처리를 통한 제목 검색 (최대 3페이지, 20개씩)
        const response = await apiService.searchBooksByTitleParallel(searchTerm, 3, 20, 3);
        
        console.log("📄 병렬 제목 검색 응답:", response);
        
        if (response.books && response.books.length > 0) {
          const processedResults = response.books.map(book => {
            let imgUrl = book.bookImageURL || book.img || "";
            if (imgUrl.includes("/book_image.jpg")) imgUrl = "/dummy-image.png";
            return {
              title: book.bookname || book.title,
              author: book.authors || book.author,
              publisher: book.publisher,
              desc: book.description || book.desc,
              img: imgUrl || "/dummy-image.png",
              isbn: book.isbn13 || book.isbn
            };
          });
          
          console.log("📚 처리된 검색 결과:", processedResults);
          setAllSearchResults(processedResults);
          setCurrentPage(1); // 페이지 리셋
          setResult(null);
        } else {
          console.log("❌ 제목 검색 결과가 없습니다.");
          setAllSearchResults([]);
          setSearchResults([]);
          setResult(null);
        }
      }
    } catch (error) {
      console.error("❌ 검색 실패:", error);
      setResult(null);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchQuery(search);
    performSearch(search);
  };

  // 모든 지역 병렬 검색 (빠른 속도)
  const searchAllRegions = async (isbn, bookTitle) => {
    console.log("🔍 모든 지역 병렬 검색 시작:", isbn);
    
    try {
      // 새로운 병렬 처리 함수 사용
      const results = await apiService.searchLibrariesByISBNParallel(isbn, [], 8);
      
      console.log(`🎉 병렬 검색 완료: 총 ${results.length}개 도서관 추출`);
      return results;
    } catch (error) {
      console.error("❌ 병렬 검색 실패:", error);
      return [];
    }
  };

  // ISBN 기반 도서관 검색 실행
  const handleLibrarySearch = async (isbn, bookTitle) => {
    if (!isbn) {
      console.log("❌ ISBN이 없어서 도서관 검색을 건너뜁니다.");
      navigate(`/library?book=${encodeURIComponent(bookTitle)}`);
      return;
    }

    console.log("🔍 ISBN 기반 도서관 검색 시작:", isbn);
    
    try {
      let response;
      let libraries = [];
      let searchType = 'single';
      
      // 전체 지역 검색
      console.log("🔍 전체 지역 병렬 검색 실행");
      libraries = await searchAllRegions(isbn, bookTitle);
      searchType = 'all';
      
      console.log("📚 ISBN 기반 도서관 검색 결과:", libraries);
      
      // 검색 결과를 URL 파라미터로 전달
      const searchParams = new URLSearchParams({
        book: bookTitle,
        isbn: isbn,
        searchType: searchType
      });
      
      // 도서관 데이터가 있으면 추가
      if (libraries.length > 0) {
        searchParams.append('libraries', JSON.stringify(libraries));
        searchParams.append('totalCount', libraries.length);
      }
      
      navigate(`/library?${searchParams.toString()}`);
      
    } catch (error) {
      console.error("❌ ISBN 기반 도서관 검색 실패:", error);
      // 에러 시 기존 방식으로 이동
      navigate(`/library?book=${encodeURIComponent(bookTitle)}`);
    }
  };

  return (
    <div className="flex flex-col items-center w-full h-full p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {/* 검색 영역 */}
      <form className="w-full max-w-xs mb-4" onSubmit={handleSearch}>
        <label className="block text-sm font-bold text-gray-700 dark:text-gray-100 mb-1">도서 정보 검색</label>
        <div className="flex">
          <input 
            type="text" 
            className="flex-1 rounded-l px-2 py-2 border border-gray-300 dark:border-gray-600 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" 
            placeholder="도서 제목 or ISBN" 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
            maxLength={30}
          />
          <button 
            type="submit" 
            className="bg-blue-600 text-white px-4 rounded-r flex items-center justify-center font-bold hover:bg-blue-700 transition"
            disabled={loading}
          >
            {loading ? "🔍" : "검색"}
          </button>
        </div>
        {searchType && (
          <div className="text-xs text-gray-500 mt-1">
            {searchType === "isbn" ? "📖 ISBN 상세조회" : "🚀 병렬 제목 검색 (3페이지)"}
          </div>
        )}
      </form>

      {/* 로딩 상태 */}
      {loading && (
        <div className="w-full max-w-xs text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">검색 중...</span>
        </div>
      )}

      {/* 검색 전: 추천도서만 */}
      {!searched && !loading && (
        <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4">
          <div className="w-full mb-2 text-center">
            <span className="inline-block text-lg font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow">추천 도서</span>
          </div>
          <FallbackImage src={dummyBooks[0].img} alt="책 표지" className="w-16 h-22 object-cover rounded-lg shadow-md mb-2" />
          <div className="flex flex-col items-center w-full">
            <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">{dummyBooks[0].title}</div>
            <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {dummyBooks[0].author}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{dummyBooks[0].desc}</div>
            <div className="flex gap-2 mt-4 w-full">
              <button 
                className="flex-1 py-2 rounded bg-blue-600 text-white font-bold hover:bg-blue-700 transition"
                onClick={() => handleLibrarySearch(dummyBooks[0].isbn, dummyBooks[0].title)}
              >
                대여하러 가기
              </button>
              <button 
                className="flex-1 py-2 rounded bg-teal-500 text-white font-bold hover:bg-teal-600 transition"
                onClick={() => navigate(`/price?query=${encodeURIComponent(dummyBooks[0].title)}`)}
              >
                가격비교
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 검색 후: 결과 표시 */}
      {searched && !loading && (
        <>
          {/* ISBN 검색 결과 (단일 도서) */}
          {searchType === "isbn" && result && (
            <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4">
              <div className="w-full mb-2 text-center">
                <span className="inline-block text-lg font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow">📖 ISBN 검색 결과</span>
              </div>
              <FallbackImage src={result.img} alt="책 표지" className="w-16 h-22 object-cover rounded-lg shadow-md mb-2" />
              <div className="flex flex-col items-center w-full">
                <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5 text-center">{result.title}</div>
                <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {result.author}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판사: {result.publisher}</div>
                {result.publication_year && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판년도: {result.publication_year}</div>
                )}
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 text-center">{result.desc}</div>
                
                {/* 대출 정보 표시 */}
                {result.loanInfo && (
                  <div className="w-full mt-2 p-2 bg-blue-50 dark:bg-blue-900 rounded-lg">
                    <div className="text-xs font-bold text-blue-700 dark:text-blue-300 mb-1">📊 대출 통계</div>
                    {result.loanInfo.Total && (
                      <div className="text-xs text-blue-600 dark:text-blue-400 mb-1">
                        전체 대출: {result.loanInfo.Total.loanCnt}회 (순위: {result.loanInfo.Total.ranking}위)
                      </div>
                    )}
                    {result.loanInfo.ageResult && result.loanInfo.ageResult.age && (
                      <div className="text-xs text-blue-600 dark:text-blue-400">
                        인기 연령대: {result.loanInfo.ageResult.age[0]?.name} ({result.loanInfo.ageResult.age[0]?.loanCnt}회)
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="flex gap-2 mt-4 w-full">
                <button className="flex-1 py-2 rounded bg-blue-600 text-white font-bold hover:bg-blue-700 transition" onClick={() => handleLibrarySearch(result.isbn, result.title)}>대여하러 가기</button>
                <button className="flex-1 py-2 rounded bg-teal-500 text-white font-bold hover:bg-teal-600 transition" onClick={() => navigate(`/price?query=${encodeURIComponent(result.title)}`)}>가격비교</button>
              </div>
            </div>
          )}

          {/* 제목 검색 결과 (도서 리스트) */}
          {searchType === "title" && searchResults.length > 0 && (
            <div className="w-full max-w-xs">
              <div className="text-center mb-3">
                <span className="text-lg font-extrabold text-purple-700 dark:text-purple-300">
                  🔍 검색 결과 ({allSearchResults.length}건 중 {searchResults.length}건 로드됨)
                </span>
              </div>
              <div className="space-y-3">
                {searchResults.map((book, index) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-lg shadow p-3">
                    <div className="flex gap-3">
                      <FallbackImage src={book.img} alt="책 표지" className="w-12 h-16 object-cover rounded shadow" />
                      <div className="flex-1">
                        <div className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-1">{book.title}</div>
                        <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {book.author}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판사: {book.publisher}</div>
                        {book.publication_year && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판년도: {book.publication_year}</div>
                        )}
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">분류: {book.desc}</div>
                        {book.loan_count && (
                          <div className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mb-1">
                            📚 대출: {parseInt(book.loan_count).toLocaleString()}회
                          </div>
                        )}
                        <div className="flex gap-1 mt-2">
                          <button 
                            className="flex-1 py-1 px-2 rounded bg-blue-600 text-white text-xs font-bold hover:bg-blue-700 transition"
                            onClick={() => handleLibrarySearch(book.isbn, book.title)}
                          >
                            대여
                          </button>
                          <button 
                            className="flex-1 py-1 px-2 rounded bg-teal-500 text-white text-xs font-bold hover:bg-teal-600 transition"
                            onClick={() => navigate(`/price?query=${encodeURIComponent(book.title)}`)}
                          >
                            가격
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* 더 보기 버튼 */}
              {hasMore && (
                <button 
                  onClick={loadMore}
                  className="w-full mt-4 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border border-violet-400"
                >
                  📚 더 많은 도서 로드 (20건 더)
                </button>
              )}
            </div>
          )}

          {/* 검색 결과 없음 */}
          {searched && !loading && ((searchType === "isbn" && !result) || (searchType === "title" && searchResults.length === 0)) && (
            <>
              <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4 text-center">
                <div className="text-lg font-extrabold text-red-600 dark:text-red-400 mb-2">🔍 검색 결과 없음</div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  "{search}"에 대한 검색 결과가 없습니다.
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500">
                  {searchType === "isbn" ? "올바른 ISBN을 입력했는지 확인해주세요." : "다른 제목으로 검색해보세요."}
                </div>
              </div>
              <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4">
                <div className="w-full mb-2 text-center">
                  <span className="inline-block text-lg font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow">추천 도서</span>
                </div>
                <FallbackImage src={dummyBooks[0].img} alt="책 표지" className="w-16 h-22 object-cover rounded-lg shadow-md mb-2" />
                <div className="flex flex-col items-center w-full">
                  <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">{dummyBooks[0].title}</div>
                  <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {dummyBooks[0].author}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{dummyBooks[0].desc}</div>
                  <div className="flex gap-2 mt-4 w-full">
                    <button 
                      className="flex-1 py-2 rounded bg-blue-600 text-white font-bold hover:bg-blue-700 transition"
                      onClick={() => handleLibrarySearch(dummyBooks[0].isbn, dummyBooks[0].title)}
                    >
                      대여하러 가기
                    </button>
                    <button 
                      className="flex-1 py-2 rounded bg-teal-500 text-white font-bold hover:bg-teal-600 transition"
                      onClick={() => navigate(`/price?query=${encodeURIComponent(dummyBooks[0].title)}`)}
                    >
                      가격비교
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
} 