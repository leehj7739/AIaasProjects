import React, { useState, useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Main from "./components/Main";
import Ocr from "./components/Ocr";
import History from "./components/History";
import Loading from "./components/Loading";
import Info from "./components/Info";
import Library from "./components/Library";

function App() {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const location = useLocation();

  // 페이지 이동 시 searchQuery 초기화 (Info 페이지가 아닐 때)
  useEffect(() => {
    if (!location.pathname.includes('/info')) {
      setSearchQuery("");
    }
  }, [location.pathname]);

  // 페이지 이동 시 스크롤을 최상단으로 이동
  useEffect(() => {
    // 메인 스크롤 컨테이너 찾기
    const scrollContainer = document.querySelector('div[class="flex-1 overflow-y-auto"]');
    if (scrollContainer) {
      scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      // fallback으로 window 스크롤 사용
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [location.pathname, location.search]); // pathname과 search 모두 변경 시 실행

  return (
    <div className="relative min-w-[320px] max-w-md w-full h-screen mx-auto bg-gray-100 dark:bg-gray-900 text-black dark:text-gray-100 flex flex-col border shadow-lg overflow-hidden">
      {/* 로딩 컴포넌트 */}
      {loading && <Loading />}
      <Header />
      <div className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/ocr" element={<Ocr loading={loading} setLoading={setLoading} setSearchQuery={setSearchQuery} />} />
          <Route path="/info" element={<Info searchQuery={searchQuery} setSearchQuery={setSearchQuery} />} />
          <Route path="/library" element={<Library />} />
          <Route path="/history" element={<History />} />
          <Route path="/" element={<Main />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}

export default App;
