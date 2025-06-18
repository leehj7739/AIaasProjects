import React from "react";
import { Link } from "react-router-dom";

const items = [
  { to: "/", icon: "🏠", label: "홈" },
  { to: "/ocr", icon: "🔍", label: "Ocr 검색" },
  { to: "/info", icon: "📖", label: "도서 검색" },
  { to: "/library", icon: "🏢", label: "도서관 검색" },
  { to: "/price", icon: "💰", label: "가격비교" },
];

export default function Footer() {
  return (
    <footer className="bg-violet-600 dark:bg-violet-900 h-16 flex items-center justify-between px-0 sm:px-2 text-white flex-shrink-0 transition-colors duration-300">
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