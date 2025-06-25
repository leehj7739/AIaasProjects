import React from "react";
import FallbackImage from "./FallbackImage";

// ISBN 검색 결과 컴포넌트
const ISBNSearchResult = ({ result, onLibrarySearch }) => (
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
          <button className="flex-1 py-3 rounded-xl bg-blue-600 text-white text-lg font-bold hover:bg-blue-700 transition shadow" onClick={() => onLibrarySearch(result.isbn, result.title)}>대여하러 가기</button>
        </div>
      </div>
    </div>
  </div>
);

// 도서 리스트 컴포넌트
const BookList = ({ books, searchType, totalCount, onLibrarySearch, onLoadMore, hasMore, keywordResponse, search }) => {
  const isKeywordSearch = searchType === "keyword";
  const bgColor = isKeywordSearch ? "bg-orange-50 dark:bg-orange-900/20" : "bg-gray-50 dark:bg-gray-800";
  const borderColor = isKeywordSearch ? "border-orange-200 dark:border-orange-700" : "";
  const titleColor = isKeywordSearch ? "text-orange-700 dark:text-orange-300" : "text-purple-700 dark:text-purple-300";
  const loadMoreColor = isKeywordSearch ? "from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 border-orange-400" : "from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 border-violet-400";

  return (
    <div className="w-full max-w-xs">
      <div className="text-center mb-3">
        <span className={`text-lg font-extrabold ${titleColor}`}>
          🔍 {searchType === "title" ? "제목" : "키워드"} 검색 결과 총 {totalCount}건
        </span>
        {isKeywordSearch && (
          <>
            <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
              제목 검색 결과가 없어서 키워드로 검색한 결과입니다
            </div>
            <div className="text-xs text-orange-500 dark:text-orange-400 mt-1 bg-orange-100 dark:bg-orange-900/30 px-2 py-1 rounded">
              🔑 검색 키워드: "{keywordResponse?.processedKeyword || search}" (원본: "{keywordResponse?.originalKeyword || search}")
            </div>
          </>
        )}
      </div>
      <div className="space-y-3">
        {books.map((book, index) => (
          <div key={index} className={`${bgColor} rounded-lg shadow p-3 ${borderColor}${index === books.length - 1 && !hasMore ? ' mb-10' : ''}`}>
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
                    onClick={() => onLibrarySearch(book.isbn, book.title)}
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
          onClick={onLoadMore}
          className={`w-full mt-4 ${isKeywordSearch ? 'pb-16' : ''} mb-0 py-3 bg-gradient-to-r ${loadMoreColor} text-white rounded-lg font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 border`}
        >
          📚 더 많은 도서 검색
        </button>
      )}
      {!hasMore && <div className="mb-2" />}
    </div>
  );
};

// 검색 결과 없음 컴포넌트
const NoResults = ({ committedSearch, searchType }) => (
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
);

// 메인 검색 결과 컴포넌트
const SearchResults = ({ 
  searched, 
  loading, 
  searchType, 
  result, 
  searchResults, 
  allSearchResults, 
  hasMore, 
  keywordResponse, 
  search, 
  committedSearch, 
  onLibrarySearch, 
  onLoadMore 
}) => {
  if (!searched || loading) return null;

  return (
    <>
      {/* ISBN 검색 결과 (단일 도서) */}
      {searchType === "isbn" && result && (
        <ISBNSearchResult result={result} onLibrarySearch={onLibrarySearch} />
      )}

      {/* 제목 검색 결과 (도서 리스트) */}
      {searchType === "title" && searchResults.length > 0 && (
        <BookList 
          books={searchResults}
          searchType="title"
          totalCount={allSearchResults.length}
          onLibrarySearch={onLibrarySearch}
          onLoadMore={onLoadMore}
          hasMore={hasMore}
        />
      )}

      {/* 키워드 검색 결과 (도서 리스트) */}
      {searchType === "keyword" && searchResults.length > 0 && (
        <BookList 
          books={searchResults}
          searchType="keyword"
          totalCount={allSearchResults.length}
          onLibrarySearch={onLibrarySearch}
          onLoadMore={onLoadMore}
          hasMore={hasMore}
          keywordResponse={keywordResponse}
          search={search}
        />
      )}

      {/* 검색 결과 없음 */}
      {searched && !loading && ((searchType === "isbn" && !result) || (searchType === "title" && searchResults.length === 0) || (searchType === "keyword" && searchResults.length === 0)) && (
        <NoResults committedSearch={committedSearch} searchType={searchType} />
      )}
    </>
  );
};

export default SearchResults; 