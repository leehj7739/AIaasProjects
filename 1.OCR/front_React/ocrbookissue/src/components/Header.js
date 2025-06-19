import React, { useState, useEffect } from "react";
import FallbackImage from "./FallbackImage";

export default function Header() {
  const [dark, setDark] = useState(false);
  const [headerHeight, setHeaderHeight] = useState("4rem");

  // 뷰포트 높이 동적 계산 (안드로이드 크롬 대응)
  useEffect(() => {
    const updateHeight = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
      
      // 안드로이드 크롬에서 주소창 높이 대응
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isChrome = /Chrome/i.test(navigator.userAgent);
      
      if (isAndroid && isChrome) {
        setHeaderHeight("5rem"); // 안드로이드 크롬에서는 더 큰 높이
      } else {
        setHeaderHeight("4rem");
      }
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    window.addEventListener('orientationchange', updateHeight);

    return () => {
      window.removeEventListener('resize', updateHeight);
      window.removeEventListener('orientationchange', updateHeight);
    };
  }, []);

  // 다크모드 토글 핸들러
  const toggleDark = () => {
    setDark((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      return next;
    });
  };

  return (
    <header className="bg-violet-600 dark:bg-violet-900 text-white flex items-center px-4 justify-between flex-shrink-0 transition-colors duration-300" style={{ height: headerHeight }}>
      <div className="flex items-center gap-2">
        <span className="text-2xl">📚</span>
        <span className="font-bold text-lg">OCR Book Issue</span>
      </div>
      <button onClick={toggleDark} className="text-2xl focus:outline-none">
        {dark ? (
          <FallbackImage src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f311.svg" alt="달" className="w-7 h-7" />
        ) : (
          <FallbackImage src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/2600.svg" alt="해" className="w-7 h-7" />
        )}
      </button>
    </header>
  );
} 