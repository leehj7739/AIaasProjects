import React from "react";

const Loading = ({ message = "업로드 중..." }) => {
  return (
    <div
      className="absolute inset-0 flex flex-col items-center justify-center z-30 shadow-2xl bg-gradient-to-br from-indigo-100 via-blue-100 to-purple-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 bg-opacity-95"
      tabIndex={0}
      aria-modal="true"
      onKeyDown={e => e.preventDefault()}
      ref={el => el && el.focus()}
    >
      <div className="relative flex flex-col items-center justify-center mb-4">
        <div className="mb-2 animate-bounce">
          <span className="text-4xl drop-shadow-lg select-none">📚</span>
        </div>
        <svg className="animate-spin h-20 w-20 text-indigo-500 drop-shadow-xl" viewBox="0 0 24 24">
          <defs>
            <radialGradient id="glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#a5b4fc" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.2" />
            </radialGradient>
          </defs>
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="url(#glow)" strokeWidth="4" fill="none" />
          <path className="opacity-90" fill="#6366f1" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      </div>
      <div className="text-indigo-700 dark:text-indigo-200 font-bold text-lg mt-2 px-6 py-3 bg-white/80 dark:bg-gray-800/80 rounded-xl shadow text-center backdrop-blur-sm">
        {message}
      </div>
    </div>
  );
};

export default Loading; 