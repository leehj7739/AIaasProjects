import React, { useState } from "react";

export default function Header() {
  const [dark, setDark] = useState(false);

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
    <header className="bg-violet-600 dark:bg-violet-900 text-white h-16 flex items-center px-4 justify-between flex-shrink-0 transition-colors duration-300">
      <div className="flex items-center gap-2">
        <span className="text-2xl">📚</span>
        <span className="font-bold text-lg">OCR Book Issue</span>
      </div>
      <button onClick={toggleDark} className="text-2xl focus:outline-none">
        {dark ? (
          <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f311.svg" alt="달" className="w-7 h-7" />
        ) : (
          <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/2600.svg" alt="해" className="w-7 h-7" />
        )}
      </button>
    </header>
  );
} 