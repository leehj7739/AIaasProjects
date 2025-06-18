import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const dummyBooks = [
  { title: "위버멘쉬", author: "프리드리히 니체", desc: "누구의 시선도 아닌, 내 의지대로 살겠다는 선언", img: "/book_image.jpg" },
  { title: "데미안", author: "헤르만 헤세", desc: "자아를 찾아가는 성장의 여정", img: "https://image.aladin.co.kr/product/32425/0/cover500/k112939963_1.jpg" },
  { title: "호밀밭의 파수꾼", author: "J.D. 샐린저", desc: "청춘의 방황과 진실에 대한 갈망", img: "https://image.aladin.co.kr/product/32425/0/cover500/k112939963_2.jpg" },
  { title: "1984", author: "조지 오웰", desc: "감시와 통제, 자유에 대한 경고", img: "https://image.aladin.co.kr/product/32425/0/cover500/k112939963_3.jpg" }
];

export default function Info({ searchQuery, setSearchQuery }) {
  const [search, setSearch] = useState("");
  const [result, setResult] = useState(null);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryParam = params.get("query");
    if (queryParam) {
      setSearchQuery(queryParam);
      setSearch(queryParam);
      setSearched(true);
      const found = dummyBooks.find(book => book.title === queryParam.trim());
      setResult(found || null);
    }
  }, [location.search, setSearchQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchQuery(search);
    setSearched(true);
    if (!search.trim()) {
      setResult(null);
      setSearchQuery("");
      setSearched(false);
      return;
    }
    const found = dummyBooks.find(book => book.title === search.trim());
    setResult(found || null);
  };

  useEffect(() => {
    setSearched(false);
  }, [search]);

  return (
    <div className="flex flex-col items-center w-full h-full p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {/* 검색 영역 */}
      <form className="w-full max-w-xs mb-4" onSubmit={handleSearch}>
        <label className="block text-sm font-bold text-gray-700 dark:text-gray-100 mb-1">도서 정보 검색</label>
        <div className="flex">
          <input type="text" className="flex-1 rounded-l px-2 py-2 border border-gray-300 dark:border-gray-600 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" placeholder="도서 제목 or ISBN" value={search} onChange={e => setSearch(e.target.value)} />
          <button type="submit" className="bg-blue-600 text-white px-4 rounded-r flex items-center justify-center font-bold hover:bg-blue-700 transition">검색</button>
        </div>
      </form>
      {/* 추천 도서 정보: 항상 노출 (검색 전에는 이것만) */}
      {!searched && (
        <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4">
          <div className="w-full mb-2 text-center">
            <span className="inline-block text-lg font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow">추천 도서</span>
          </div>
          <img src={dummyBooks[0].img} alt="책 표지" className="w-16 h-22 object-cover rounded-lg shadow-md mb-2" />
          <div className="flex flex-col items-center w-full">
            <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">{dummyBooks[0].title}</div>
            <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {dummyBooks[0].author}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{dummyBooks[0].desc}</div>
            <div className="flex gap-2 mt-4 w-full">
              <button 
                className="flex-1 py-2 rounded bg-blue-600 text-white font-bold hover:bg-blue-700 transition"
                onClick={() => navigate(`/library?book=${encodeURIComponent(dummyBooks[0].title)}`)}
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
      {/* 검색 결과/없음/추천도서: 검색 후에만 노출 */}
      {searched && (
        <>
          {result === null && search.trim() !== "" ? (
            <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4 text-center text-gray-500">
              검색 결과가 없습니다.
            </div>
          ) : result ? (
            <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4">
              <div className="w-full mb-2 text-center">
                <span className="inline-block text-lg font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow">검색 결과</span>
              </div>
              <img src={result.img || "/book_image.jpg"} alt="책 표지" className="w-16 h-22 object-cover rounded-lg shadow-md mb-2" />
              <div className="flex flex-col items-center w-full">
                <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">{result.title}</div>
                <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {result.author}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{result.desc}</div>
              </div>
              <div className="flex gap-2 mt-4 w-full">
                <button className="flex-1 py-2 rounded bg-blue-600 text-white font-bold hover:bg-blue-700 transition" onClick={() => navigate(`/library?book=${encodeURIComponent(result.title)}`)}>대여하러 가기</button>
                <button className="flex-1 py-2 rounded bg-teal-500 text-white font-bold hover:bg-teal-600 transition" onClick={() => navigate(`/price?query=${encodeURIComponent(result.title)}`)}>가격비교</button>
              </div>
            </div>
          ) : null}
          {/* 추천 도서는 검색 결과가 없을 때만 표시 */}
          {(result === null || !result) && (
            <div className="w-full max-w-xs mx-auto bg-gray-50 dark:bg-gray-800 rounded-xl shadow-lg flex flex-col items-center p-3 mb-4">
              <div className="w-full mb-2 text-center">
                <span className="inline-block text-lg font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow">추천 도서</span>
              </div>
              <img src={dummyBooks[0].img} alt="책 표지" className="w-16 h-22 object-cover rounded-lg shadow-md mb-2" />
              <div className="flex flex-col items-center w-full">
                <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">{dummyBooks[0].title}</div>
                <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {dummyBooks[0].author}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{dummyBooks[0].desc}</div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
} 