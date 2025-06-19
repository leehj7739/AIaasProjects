import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const items = [
  { to: "/", icon: "🏠", label: "홈" },
  { to: "/ocr", icon: "🔍", label: "Ocr 검색" },
  { to: "/info", icon: "📖", label: "도서 검색" },
  { to: "/library", icon: "🏢", label: "도서관 검색" },
  { to: "/price", icon: "💰", label: "가격비교" },
];

export default function Footer() {
  const [footerHeight, setFooterHeight] = useState("4rem");

  // 뷰포트 높이 동적 계산 (안드로이드 크롬 대응)
  useEffect(() => {
    const updateHeight = () => {
      // 안드로이드 크롬에서 하단 버튼 영역 대응
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isChrome = /Chrome/i.test(navigator.userAgent);
      
      if (isAndroid && isChrome) {
        setFooterHeight("5rem"); // 안드로이드 크롬에서는 더 큰 높이
      } else {
        setFooterHeight("4rem");
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

  return (
    <footer className="bg-violet-600 dark:bg-violet-900 flex items-center justify-between px-0 sm:px-2 text-white flex-shrink-0 transition-colors duration-300" style={{ height: footerHeight }}>
      {items.map((item, idx) => (
        <React.Fragment key={idx}>
          {item.to.startsWith("/") ? (
            <Link to={item.to === "#" && idx === items.length - 1 ? "/price" : item.to} className="flex-1 flex flex-col items-center justify-center">
              <span className="text-2xl">{item.icon}</span>
              <span className="text-xs mt-0.5 text-white dark:text-gray-200">{item.label}</span>
            </Link>
          ) : (
            <button className="flex-1 flex flex-col items-center justify-center">
              <span className="text-2xl">{item.icon}</span>
              <span className="text-xs mt-0.5 text-white dark:text-gray-200">{item.label}</span>
            </button>
          )}
          {idx < items.length - 1 && (
            <div className="h-8 w-px bg-violet-200 dark:bg-violet-800 mx-0.5" />
          )}
        </React.Fragment>
      ))}
    </footer>
  );
} 