import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { apiService } from "../services/api";
import FallbackImage from "./FallbackImage";
import { HiXCircle } from "react-icons/hi2";
import Loading from "./Loading";

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

// 검색 히스토리 저장 함수
const saveBookHistory = (query, type, title = "") => {
  let history = JSON.parse(localStorage.getItem('bookHistory') || '[]');
  history = history.filter(item => !(item.query === query && item.type === type));
  history.unshift({
    id: Date.now() + Math.random().toString(36).slice(2),
    query,
    type, // 'isbn', 'title', 'keyword', '검색실패'
    title, // isbn 검색 시 책 제목 저장
    createdAt: new Date().toISOString()
  });
  localStorage.setItem('bookHistory', JSON.stringify(history.slice(0, 20)));
};

export default function Info({ searchQuery, setSearchQuery }) {
  const [search, setSearch] = useState("");
  const [committedSearch, setCommittedSearch] = useState("");
  const [result, setResult] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState(""); // "isbn" 또는 "keyword"
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [allSearchResults, setAllSearchResults] = useState([]);
  const [keywordResponse, setKeywordResponse] = useState(null); // 키워드 검색 응답 저장
  const navigate = useNavigate();
  const location = useLocation();

  // 페이지당 아이템 수
  const ITEMS_PER_PAGE = 20;

  // 검색 결과 메모이제이션
  const currentSearchResults = useMemo(() => {
    if (allSearchResults.length > 0) {
      const startIndex = 0;
      const endIndex = currentPage * ITEMS_PER_PAGE;
      return allSearchResults.slice(startIndex, endIndex);
    }
    return [];
  }, [allSearchResults, currentPage]);

  const hasMoreResults = useMemo(() => {
    return currentSearchResults.length < allSearchResults.length;
  }, [currentSearchResults.length, allSearchResults.length]);

  // 검색 타입 표시 메모이제이션
  const searchTypeDisplay = useMemo(() => {
    if (!searchType) return "";
    
    switch (searchType) {
      case "isbn":
        return "📖 ISBN 도서 검색";
      case "title":
        return "🚀 도서제목 검색";
      case "keyword":
        return "🔍 키워드 검색";
      default:
        return "";
    }
  }, [searchType]);

  // 페이지 변경 시 검색 결과 업데이트
  useEffect(() => {
    setSearchResults(currentSearchResults);
    setHasMore(hasMoreResults);
  }, [currentSearchResults, hasMoreResults]);

  // 페이지 진입 시 상태 초기화
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryParam = params.get("query");
    
    // URL 파라미터가 없으면 모든 상태 초기화
    if (!queryParam) {
      setSearch("");
      setCommittedSearch("");
      setResult(null);
      setSearchResults([]);
      setSearched(false);
      setLoading(false);
      setSearchType("");
      setCurrentPage(1);
      setHasMore(false);
      setAllSearchResults([]);
      setKeywordResponse(null);
    }
  }, [location.pathname]); // pathname이 변경될 때만 실행

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

  // searchQuery prop이 변경될 때 자동으로 검색 실행
  useEffect(() => {
    if (searchQuery && searchQuery.trim()) {
      setSearch(searchQuery);
      setSearched(true);
      // performSearch 함수가 정의된 후에 호출되도록 setTimeout 사용
      setTimeout(() => {
        performSearch(searchQuery);
      }, 0);
    }
  }, [searchQuery]);

  const performSearch = useCallback(async (searchTerm) => {
    if (!searchTerm.trim()) {
      setResult(null);
      setSearchResults([]);
      setSearched(false);
      setSearchType("");
      setKeywordResponse(null); // 키워드 응답도 리셋
      return;
    }

    setResult(null); // 검색 시작 시 바로 초기화
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
        
        // 응답 구조에 따른 데이터 추출
        let bookData = null;
        let loanInfo = null;
        
        if (response.data?.response?.detail) {
          // detail이 배열일 수도 있고 객체일 수도 있음
          const detail = Array.isArray(response.data.response.detail)
            ? response.data.response.detail[0]
            : response.data.response.detail;
          bookData = detail.book;
          loanInfo = response.data.response.loanInfo;
        } else if (response.data?.response?.book) {
          bookData = response.data.response.book;
          loanInfo = response.data.response.loanInfo;
        } else if (response.data?.response?.docs?.doc) {
          const docs = Array.isArray(response.data.response.docs.doc) 
            ? response.data.response.docs.doc 
            : [response.data.response.docs.doc];
          if (docs.length > 0) {
            bookData = docs[0];
          }
        } else if (response.data?.response) {
          bookData = response.data.response;
        }
        
        console.log("📚 추출된 도서 데이터:", bookData);
        console.log("📊 대출 정보:", loanInfo);
        
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
          saveBookHistory(searchTerm, 'isbn', resultData.title);
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
          saveBookHistory(searchTerm, 'title');
        } else {
          console.log("❌ 제목 검색 결과가 없습니다. 키워드 검색을 시도합니다.");
          
          // 제목 검색 결과가 없으면 키워드 검색 실행
          console.log("🔍 키워드 검색 실행:", searchTerm);
          setSearchType("keyword");
          
          const keywordResponse = await apiService.searchBooksByKeywordParallel(searchTerm, 3, 20, 3);
          
          console.log("📄 병렬 키워드 검색 응답:", keywordResponse);
          
          // 키워드 검색 응답 저장
          setKeywordResponse(keywordResponse);
          
          if (keywordResponse.books && keywordResponse.books.length > 0) {
            const processedKeywordResults = keywordResponse.books.map(book => {
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
            
            console.log("📚 키워드 검색 결과:", processedKeywordResults);
            setAllSearchResults(processedKeywordResults);
            setCurrentPage(1); // 페이지 리셋
            setResult(null);
            saveBookHistory(searchTerm, 'keyword');
          } else {
            console.log("❌ 키워드 검색 결과도 없습니다.");
            setAllSearchResults([]);
            setSearchResults([]);
            setResult(null);
            setKeywordResponse(null); // 키워드 응답도 리셋
            saveBookHistory(searchTerm, '검색실패');
          }
        }
      }
    } catch (error) {
      console.error("❌ 검색 실패:", error);
      setResult(null);
      setSearchResults([]);
      setKeywordResponse(null); // 키워드 응답도 리셋
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSearch = useCallback((e) => {
    e.preventDefault();
    setSearched(true);
    setCommittedSearch(search);
    setSearchQuery(search);
    performSearch(search);
  }, [search, setSearchQuery, performSearch]);

  // 모든 지역 병렬 검색 (빠른 속도)
  const searchAllRegions = useCallback(async (isbn, bookTitle) => {
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
  }, []);

  // ISBN 기반 도서관 검색 실행
  const handleLibrarySearch = useCallback(async (isbn, bookTitle) => {
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
  }, [navigate, searchAllRegions]);

  return (
    <div className="flex flex-col items-center w-full min-h-screen p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {loading && <Loading message="도서 정보를 불러오는 중..." />}
      {/* 검색 영역 */}
      <form className="w-full max-w-xs mb-4" onSubmit={handleSearch}>
        <label className="block text-sm font-bold text-gray-700 dark:text-gray-100 mb-1">도서 정보 검색</label>
        <div className="flex">
          <div className="relative flex-1">
            <input 
              type="text" 
              className="w-full rounded-l px-2 py-2 border border-gray-300 dark:border-gray-600 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 pr-8" 
              placeholder="도서제목 또는 ISBN을 입력해 주세요" 
              value={search} 
              onChange={e => setSearch(e.target.value)} 
              maxLength={30}
            />
            {search && (
              <button
                type="button"
                className="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-full bg-transparent border-none p-0 text-gray-400 hover:text-gray-600 focus:outline-none"
                onClick={() => setSearch("")}
                tabIndex={-1}
                aria-label="입력 지우기"
              >
                <HiXCircle className="w-5 h-5" />
              </button>
            )}
          </div>
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
            {searchTypeDisplay}
          </div>
        )}
      </form>

      {/* 검색 전: 빈 상태 */}
      {!searched && !loading && (
        <div className="w-full max-w-xs mx-auto text-center py-8">
          <div className="text-lg text-gray-600 dark:text-gray-400">
            🔍 도서를 검색해보세요
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            제목, ISBN, 키워드로 검색할 수 있습니다
          </div>
        </div>
      )}

      {/* 검색 후: 결과 표시 */}
      {searched && !loading && (
        <>
          {/* ISBN 검색 결과 (단일 도서) */}
          {searchType === "isbn" && result && (
            <div className="w-full max-w-md mx-auto">
              <div className="text-center mb-4">
                <span className="text-2xl font-extrabold text-purple-700 dark:text-purple-300 drop-shadow">ISBN 검색 결과</span>
              </div>
              <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 flex flex-col md:flex-row gap-6 items-center border border-purple-200 dark:border-purple-800 mb-8">
                <div className="flex-shrink-0">
                  <FallbackImage src={result.img} alt="책 표지" className="w-40 h-56 object-cover rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 bg-white" />
                </div>
                <div className="flex-1 flex flex-col gap-2 w-full">
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1 leading-tight">{result.title}</div>
                  <div className="text-base text-gray-700 dark:text-gray-300 mb-1">저자: <span className="font-semibold">{(result.author || '').replace(/^(저자|지은이)\s*:\s*/g, '').replace(/^(저자|지은이)\s*:\s*/g, '')}</span></div>
                  <div className="text-base text-gray-700 dark:text-gray-300 mb-1">출판사: <span className="font-semibold">{result.publisher}</span></div>
                  {result.publication_year && (
                    <div className="text-base text-gray-500 dark:text-gray-400 mb-1">출판년도: {result.publication_year}</div>
                  )}
                  <div className="text-base text-gray-500 dark:text-gray-400 mb-1">ISBN: {result.isbn}</div>
                  {result.desc && (
                    <div className="text-base text-gray-600 dark:text-gray-300 mt-2 whitespace-pre-line">{result.desc}</div>
                  )}
                  {/* 대출 정보 표시: 정보가 있을 때만 */}
                  {result.loanInfo && (result.loanInfo.Total || (result.loanInfo.ageResult && result.loanInfo.ageResult.age)) && (
                    <div className="w-full mt-3 p-3 bg-blue-50 dark:bg-blue-900 rounded-lg">
                      <div className="text-sm font-bold text-blue-700 dark:text-blue-300 mb-1">📊 대출 통계</div>
                      {result.loanInfo.Total && (
                        <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                          전체 대출: {result.loanInfo.Total.loanCnt}회 (순위: {result.loanInfo.Total.ranking}위)
                        </div>
                      )}
                      {result.loanInfo.ageResult && result.loanInfo.ageResult.age && (
                        <div className="text-sm text-blue-600 dark:text-blue-400">
                          인기 연령대: {result.loanInfo.ageResult.age[0]?.name} ({result.loanInfo.ageResult.age[0]?.loanCnt}회)
                        </div>
                      )}
                    </div>
                  )}
                  <div className="flex gap-3 mt-6">
                    <button className="flex-1 py-3 rounded-xl bg-blue-600 text-white text-lg font-bold hover:bg-blue-700 transition shadow" onClick={() => handleLibrarySearch(result.isbn, result.title)}>대여하러 가기</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 제목 검색 결과 (도서 리스트) */}
          {searchType === "title" && searchResults.length > 0 && (
            <div className="w-full max-w-xs">
              <div className="text-center mb-3">
                <span className="text-lg font-extrabold text-purple-700 dark:text-purple-300">
                  🔍 제목 검색 결과 총 {allSearchResults.length}건
                </span>
              </div>
              <div className="space-y-3">
                {searchResults.map((book, index) => (
                  <div key={index} className={`bg-gray-50 dark:bg-gray-800 rounded-lg shadow p-3${index === searchResults.length - 1 && !hasMore ? ' mb-10' : ''}`}>
                    <div className="flex gap-3">
                      <FallbackImage src={book.img} alt="책 표지" className="w-12 h-16 object-cover rounded shadow" />
                      <div className="flex-1">
                        <div className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-1">{book.title}</div>
                        <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {book.author}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판사: {book.publisher}</div>
                        {book.publication_year && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판년도: {book.publication_year}</div>
                        )}
                        {book.desc && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">분류: {book.desc}</div>
                        )}
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
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* 더 보기 버튼 */}
              {hasMore && (
                <button 
                  onClick={() => setCurrentPage(prev => prev + 1)}
                  className="w-full mt-4 mb-4 pb-3 mb-0 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border border-violet-400"
                >
                  📚 더 많은 도서 검색
                </button>
              )}
              {!hasMore && <div className="mb-2" />}
            </div>
          )}

          {/* 키워드 검색 결과 (도서 리스트) */}
          {searchType === "keyword" && searchResults.length > 0 && (
            <div className="w-full max-w-xs">
              <div className="text-center mb-3">
                <span className="text-lg font-extrabold text-orange-700 dark:text-orange-300">
                  🔍 키워드 검색 결과 : 총 {allSearchResults.length}건
                </span>
                <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                  제목 검색 결과가 없어서 키워드로 검색한 결과입니다
                </div>
                <div className="text-xs text-orange-500 dark:text-orange-400 mt-1 bg-orange-100 dark:bg-orange-900/30 px-2 py-1 rounded">
                  🔑 검색 키워드: "{keywordResponse?.processedKeyword || search}" (원본: "{keywordResponse?.originalKeyword || search}")
                </div>
              </div>
              <div className="space-y-3">
                {searchResults.map((book, index) => (
                  <div key={index} className={`bg-orange-50 dark:bg-orange-900/20 rounded-lg shadow p-3 border border-orange-200 dark:border-orange-700${index === searchResults.length - 1 && !hasMore ? ' mb-10' : ''}`}>
                    <div className="flex gap-3">
                      <FallbackImage src={book.img} alt="책 표지" className="w-12 h-16 object-cover rounded shadow" />
                      <div className="flex-1">
                        <div className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-1">{book.title}</div>
                        <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {book.author}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판사: {book.publisher}</div>
                        {book.publication_year && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">출판년도: {book.publication_year}</div>
                        )}
                        {book.desc && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">분류: {book.desc}</div>
                        )}
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
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* 더 보기 버튼 */}
              {hasMore && (
                <button 
                  onClick={() => setCurrentPage(prev => prev + 1)}
                  className="w-full mt-4 pb-16 mb-0 py-3 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border border-orange-400"
                >
                  📚 더 많은 도서 검색
                </button>
              )}
              {!hasMore && <div className="mb-2" />}
            </div>
          )}

          {/* 검색 결과 없음 */}
          {searched && !loading && ((searchType === "isbn" && !result) || (searchType === "title" && searchResults.length === 0) || (searchType === "keyword" && searchResults.length === 0)) && (
            <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4 text-center">
              <div className="text-lg font-extrabold text-red-600 dark:text-red-400 mb-2">🔍 검색 결과 없음</div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                "{committedSearch}"에 대한 검색 결과가 없습니다.
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-500">
                {searchType === "isbn" ? "올바른 ISBN을 입력했는지 확인해주세요." : 
                 searchType === "title" ? "제목 검색 후 키워드 검색도 시도했지만 결과가 없습니다." :
                 searchType === "keyword" ? "제목 검색과 키워드 검색 모두 시도했지만 결과가 없습니다." : 
                 "다른 검색어로 시도해보세요."}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
} 