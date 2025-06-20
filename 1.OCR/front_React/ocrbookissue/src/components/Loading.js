import React from "react";

const Loading = ({ message = "업로드 중..." }) => {
  return (
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
      <div className="text-white font-bold text-lg mt-4">{message}</div>
    </div>
  );
};

export default Loading; 