import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

const dummyPrices = [
  { mall: "교보문고", price: 12000, url: "https://www.kyobobook.co.kr", logo: "/favicon.ico" },
  { mall: "YES24", price: 11500, url: "https://www.yes24.com", logo: "/favicon.ico" },
  { mall: "알라딘", price: 11000, url: "https://www.aladin.co.kr", logo: "/favicon.ico" },
  { mall: "인터파크", price: 11800, url: "https://book.interpark.com", logo: "/favicon.ico" },
];

export default function Price() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryParam = params.get("query");
    if (queryParam) {
      setQuery(queryParam);
      setResults([...dummyPrices].sort((a, b) => a.price - b.price));
    }
  }, [location.search]);

  const handleSearch = () => {
    // 실제 검색 API 연동 대신 더미 데이터 사용, 가격순 정렬
    setResults([...dummyPrices].sort((a, b) => a.price - b.price));
  };

  return (
    <div className="flex flex-col items-center w-full h-full p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      <div className="w-full max-w-xs mb-4">
        <label className="block text-sm font-bold text-gray-700 dark:text-gray-100 mb-1">도서 가격 검색</label>
        <div className="flex">
          <input
            type="text"
            className="flex-1 rounded-l px-2 py-2 border border-gray-300 dark:border-gray-600 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            placeholder="도서 제목 or ISBN"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <button
            className="bg-blue-600 text-white px-4 rounded-r flex items-center justify-center font-bold hover:bg-blue-700"
            onClick={handleSearch}
          >
            검색
          </button>
        </div>
      </div>
      {/* 가격 리스트 */}
      {results.length > 0 && (
        <div className="w-full max-w-xs bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg p-3 mt-2">
          <div className="mb-2 text-center text-base font-bold text-purple-700 dark:text-purple-300">쇼핑몰별 최저가</div>
          <ul className="flex flex-col gap-2">
            {results.map((item, idx) => (
              <li key={item.mall} className="flex items-center justify-between bg-white dark:bg-gray-700 rounded p-2 shadow flex-nowrap">
                <span className="w-2/5 text-left font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                  <img src={item.logo} alt={item.mall + ' 로고'} className="w-5 h-5 rounded bg-white border mr-1" />
                  {item.mall}
                </span>
                <span className="w-2/5 text-right text-blue-600 dark:text-blue-300 font-bold">{item.price.toLocaleString()}원</span>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs font-bold transition whitespace-nowrap"
                >
                  이동
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
} 