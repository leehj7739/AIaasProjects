import React from "react";

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

// 지역명 축약형 변환 함수
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

// 도서관 카드 컴포넌트
const LibraryCard = ({ library, index, isLast, hasMore }) => {
  const displayLib = library.lib || library;
  const region = displayLib.region || displayLib.regionName || (displayLib.address ? displayLib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
  const shortRegion = getShortRegionName(region);
  const regionColor = getRegionColor(shortRegion);

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 border border-gray-200 dark:border-gray-700${index === isLast && !hasMore ? ' mb-10' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">
            {displayLib.libName}
          </h3>
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 rounded-full text-xs font-bold ${regionColor}`}>
              {shortRegion}
            </span>
            {displayLib.bookCount && (
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                📚 {displayLib.bookCount}권 보유
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        {displayLib.address && (
          <div className="flex items-start gap-2">
            <span className="text-gray-500 dark:text-gray-400 w-16 flex-shrink-0">📍 주소:</span>
            <span className="text-gray-700 dark:text-gray-300 flex-1">{displayLib.address}</span>
          </div>
        )}
        
        {(displayLib.tel || displayLib.phone) && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400 w-16 flex-shrink-0">📞 전화:</span>
            <span className="text-gray-700 dark:text-gray-300">{displayLib.tel || displayLib.phone}</span>
          </div>
        )}
        
        {displayLib.homepage && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400 w-16 flex-shrink-0">🌐 홈페이지:</span>
            <a 
              href={displayLib.homepage} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline truncate"
            >
              {displayLib.homepage}
            </a>
          </div>
        )}
        
        {displayLib.operatingTime && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400 w-16 flex-shrink-0">🕒 운영시간:</span>
            <span className="text-gray-700 dark:text-gray-300">{displayLib.operatingTime}</span>
          </div>
        )}
        
        {displayLib.closed && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400 w-16 flex-shrink-0">🚫 휴관일:</span>
            <span className="text-gray-700 dark:text-gray-300">{displayLib.closed}</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ISBN 검색 결과 헤더 컴포넌트
const ISBNSearchHeader = ({ isbnInfo, onClearISBNResults }) => (
  <div className="w-full max-w-md mx-auto mb-6">
    <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-4 text-white">
      <div className="text-center">
        <div className="text-lg font-bold mb-2">🔍 ISBN 기반 도서관 검색</div>
        <div className="text-sm mb-1">도서: {isbnInfo.bookTitle}</div>
        <div className="text-xs opacity-90">ISBN: {isbnInfo.isbn}</div>
      </div>
      <button 
        onClick={onClearISBNResults}
        className="mt-3 w-full bg-white/20 hover:bg-white/30 text-white py-2 px-4 rounded-lg font-bold transition"
      >
        🔄 새로운 검색
      </button>
    </div>
  </div>
);

// 일반 검색 헤더 컴포넌트
const GeneralSearchHeader = ({ totalCount, searchQuery, onShowCachedList, onClearCacheAndRefresh }) => (
  <div className="w-full max-w-md mx-auto mb-6">
    <div className="bg-gradient-to-r from-green-500 to-teal-600 rounded-xl shadow-lg p-4 text-white">
      <div className="text-center">
        <div className="text-lg font-bold mb-2">🏛️ 도서관 검색 결과</div>
        <div className="text-sm mb-1">총 {totalCount}개 도서관</div>
        {searchQuery && (
          <div className="text-xs opacity-90">검색어: "{searchQuery}"</div>
        )}
      </div>
      <div className="flex gap-2 mt-3">
        <button 
          onClick={onShowCachedList}
          className="flex-1 bg-white/20 hover:bg-white/30 text-white py-2 px-4 rounded-lg font-bold transition text-sm"
        >
          📋 전체 목록
        </button>
        <button 
          onClick={onClearCacheAndRefresh}
          className="flex-1 bg-white/20 hover:bg-white/30 text-white py-2 px-4 rounded-lg font-bold transition text-sm"
        >
          🔄 새로고침
        </button>
      </div>
    </div>
  </div>
);

// 메인 도서관 결과 컴포넌트
const LibraryResults = ({ 
  libraries, 
  displayLibraries, 
  loading, 
  error, 
  isISBNSearch, 
  isbnInfo, 
  searchQuery, 
  totalCount, 
  hasMore, 
  onLoadMore, 
  onClearISBNResults, 
  onShowCachedList, 
  onClearCacheAndRefresh 
}) => {
  if (loading) {
    return (
      <div className="w-full max-w-xs text-center py-4">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">도서관 정보를 불러오는 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-xs text-center py-2 text-red-600 dark:text-red-400 text-sm">{error}</div>
    );
  }

  if (!displayLibraries || displayLibraries.length === 0) {
    return (
      <div className="w-full max-w-xs text-center py-8 text-gray-500 dark:text-gray-400">검색 결과가 없습니다.</div>
    );
  }

  return (
    <ul className="w-full max-w-xs flex flex-col gap-3 mt-2">
      {displayLibraries.map((lib, idx) => {
        let region = '기타';
        let shortRegion = '기타';
        const displayLib = lib.lib || lib;
        if (lib.lib) {
          region = lib.lib.region || lib.lib.regionName || (lib.lib.address ? lib.lib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
          shortRegion = getShortRegionName(region);
        } else {
          region = lib.region || lib.regionName || (lib.address ? lib.address.split(' ')[0].replace(/특별시|광역시|도/g, '') : '기타');
          shortRegion = getShortRegionName(region);
        }
        return (
          <li key={displayLib.libCode || idx} className="bg-white dark:bg-gray-900 rounded-lg shadow p-4 flex flex-col gap-1 relative">
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
  );
};

export default LibraryResults; 