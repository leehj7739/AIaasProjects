import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Main from "./components/Main";
import Ocr from "./components/Ocr";
import Info from "./components/Info";
import Price from "./components/Price";
import Library from "./components/Library";

function App() {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="relative min-w-[320px] max-w-md w-full h-screen mx-auto bg-gray-100 dark:bg-gray-900 text-black dark:text-gray-100 flex flex-col border shadow-lg overflow-hidden">
      {/* 전체 오버레이 + 스피너 */}
      {loading && (
        <div
          className="absolute inset-0 bg-black bg-opacity-60 flex flex-col items-center justify-center z-30"
          tabIndex={0}
          aria-modal="true"
          onKeyDown={e => e.preventDefault()}
          ref={el => el && el.focus()}
        >
          <div className="relative flex items-center justify-center">
            <svg className="animate-spin h-24 w-24 text-blue-700 drop-shadow-lg relative" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="#2563eb" strokeWidth="4" fill="none" />
              <path className="opacity-90" fill="#2563eb" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
          </div>
          <div className="text-white font-bold text-lg mt-4">업로드 중...</div>
        </div>
      )}
      <Header />
      <div className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/ocr" element={<Ocr loading={loading} setLoading={setLoading} setSearchQuery={setSearchQuery} />} />
          <Route path="/info" element={<Info searchQuery={searchQuery} setSearchQuery={setSearchQuery} />} />
          <Route path="/price" element={<Price />} />
          <Route path="/library" element={<Library />} />
          <Route path="/" element={<Main />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}

export default App;
