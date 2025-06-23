import React, { useState, useEffect } from "react";
import UploadModeToggle from "./UploadModeToggle";
import Ocr from "./Ocr";
import { useNavigate } from "react-router-dom";

const options = [
  { label: "OCR 검색", value: "ocr" },
  { label: "도서검색", value: "book" },
  { label: "도서관검색", value: "library" },
];

export default function History() {
  const [activeMode, setActiveMode] = useState("ocr");
  const [ocrHistory, setOcrHistory] = useState([]);
  const [selectedOcr, setSelectedOcr] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (activeMode === "ocr") {
      const history = JSON.parse(localStorage.getItem('ocrHistory') || '[]');
      setOcrHistory(history);
    }
  }, [activeMode]);

  // OCR 히스토리 삭제 함수
  const handleDelete = (id) => {
    const newHistory = ocrHistory.filter(item => item.id !== id);
    setOcrHistory(newHistory);
    localStorage.setItem('ocrHistory', JSON.stringify(newHistory));
  };

  // 검색 쿼리 상태(상위 App에서 내려주는 props가 없으므로 localStorage 활용)
  const setSearchQuery = (query) => {
    localStorage.setItem('searchQuery', query);
  };

  return (
    <div className="flex flex-col items-center w-full min-h-screen p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      <h1 className="text-2xl font-bold mb-6 mt-2">히스토리</h1>
      <UploadModeToggle options={options} mode={activeMode} setMode={setActiveMode} />
      <div className="w-full max-w-md bg-blue-50 dark:bg-gray-800 rounded-xl shadow p-3 min-h-[200px]">
        {activeMode === "ocr" ? (
          ocrHistory.length === 0 ? (
            <div className="text-center text-gray-400">OCR 기록이 없습니다.</div>
          ) : (
            <ul className="space-y-1.5">
              {ocrHistory.map(item => (
                <li
                  key={item.id}
                  className="flex gap-3 items-center p-3 bg-white dark:bg-gray-900 rounded-xl shadow group transition cursor-pointer border border-gray-100 dark:border-gray-700 hover:bg-violet-50 dark:hover:bg-violet-900/40"
                >
                  <img src={item.ocrResultImageUrl || item.originalImageUrl} alt="썸네일" className="w-12 h-12 object-cover rounded" onClick={() => setSelectedOcr(item)} />
                  <div className="flex-1" onClick={() => setSelectedOcr(item)}>
                    <div className="font-bold truncate max-w-[180px]">{item.extractedText}</div>
                    <div className="text-xs text-gray-500">{item.createdAt && new Date(item.createdAt).toLocaleString()}</div>
                  </div>
                  {/* 검색 버튼 (파란색 원형) */}
                  <button
                    className="ml-2 w-8 h-8 flex items-center justify-center rounded-full bg-blue-500 hover:bg-blue-700 text-white text-lg font-bold shadow transition"
                    title="이 책 제목으로 검색"
                    onClick={e => {
                      e.stopPropagation();
                      setSearchQuery(item.extractedText);
                      navigate('/info');
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 104.5 4.5a7.5 7.5 0 0012.15 12.15z" />
                    </svg>
                  </button>
                  {/* 삭제 버튼 (빨간색 원형) */}
                  <button
                    className="ml-2 w-8 h-8 flex items-center justify-center rounded-full bg-red-500 hover:bg-red-700 text-white text-lg font-bold shadow transition"
                    title="삭제"
                    onClick={e => { e.stopPropagation(); handleDelete(item.id); }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
          )
        ) : (
          <div className="text-center text-gray-400">아직 구현되지 않은 메뉴입니다.</div>
        )}
      </div>
      {/* OCR 상세 결과 모달 */}
      {selectedOcr && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6 max-w-2xl w-full relative">
            <button className="absolute top-2 right-2 text-2xl text-gray-400 hover:text-red-500" onClick={() => setSelectedOcr(null)}>×</button>
            <Ocr viewMode ocrData={selectedOcr} />
          </div>
        </div>
      )}
    </div>
  );
} 