import React, { useState } from "react";
import UploadModeToggle from "./UploadModeToggle";

const dummyHistory = {
  ocr: [
    { id: 1, text: "해리포터와 마법사의 돌 (OCR)" },
    { id: 2, text: "데미안 (OCR)" },
  ],
  book: [
    { id: 1, text: "위버멘쉬" },
    { id: 2, text: "데미안" },
    { id: 3, text: "호밀밭의 파수꾼" },
  ],
  library: [
    { id: 1, text: "서울도서관" },
    { id: 2, text: "경기중앙도서관" },
  ],
};

const options = [
  { label: "OCR 검색", value: "ocr" },
  { label: "도서검색", value: "book" },
  { label: "도서관검색", value: "library" },
];

export default function History() {
  const [activeMode, setActiveMode] = useState("ocr");

  return (
    <div className="flex flex-col items-center w-full min-h-screen p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      <h1 className="text-2xl font-bold mb-6 mt-2">히스토리</h1>
      <UploadModeToggle options={options} mode={activeMode} setMode={setActiveMode} />
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow p-6 min-h-[200px]">
        {dummyHistory[activeMode].length === 0 ? (
          <div className="text-center text-gray-400">기록이 없습니다.</div>
        ) : (
          <ul className="space-y-2">
            {dummyHistory[activeMode].map(item => (
              <li key={item.id} className="border-b border-gray-200 dark:border-gray-700 py-2 last:border-b-0">
                {item.text}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
} 