import React, { useState } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Main from "./components/Main";
import Ocr from "./components/Ocr";
import Info from "./components/Info";
import Library from "./components/Library";
import Loading from "./components/Loading";
import History from "./components/History";

function App() {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const location = useLocation();

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
