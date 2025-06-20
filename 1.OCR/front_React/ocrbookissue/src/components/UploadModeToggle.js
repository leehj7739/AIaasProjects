import React from "react";

/**
 * options: [{ label: '이미지 업로드', value: 'image' }, { label: 'URL 업로드', value: 'url' }]
 * mode: 현재 선택된 값
 * setMode: 값 변경 함수
 * loading: 비활성화 여부
 */
const UploadModeToggle = ({ options, mode, setMode, loading }) => (
  <div className={`flex gap-2 mb-4 w-full max-w-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 p-1 transition-colors duration-200 ${loading ? "pointer-events-none opacity-60" : ""}` }>
    {options.map(opt => (
      <button
        key={opt.value}
        className={`flex-1 py-2 rounded-md font-bold transition-colors duration-200 ${mode === opt.value ? "bg-blue-600 text-white shadow" : "bg-transparent text-gray-700 dark:text-gray-200"}`}
        onClick={() => setMode(opt.value)}
        disabled={loading}
      >
        {opt.label}
      </button>
    ))}
  </div>
);

export default UploadModeToggle; 