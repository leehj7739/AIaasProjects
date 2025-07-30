import React from 'react';

const ChatInput = ({ input, onChange, onSend, disabled = false }) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !disabled) {
      onSend();
    }
  };

  return (
    <div className="bg-white px-2 py-2 flex items-center border-t border-gray-300">
      <input
        type="text"
        className={`flex-1 rounded-full border border-gray-300 px-4 py-2 mr-2 focus:outline-none focus:border-blue-400 text-sm ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
        placeholder={disabled ? "연결을 확인해주세요..." : "input chatting..."}
        value={input}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button
        className={`w-8 h-8 rounded-full flex items-center justify-center text-white transition-colors duration-200 ${disabled
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700'
          }`}
        onClick={onSend}
        disabled={disabled}
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </button>
    </div>
  );
};

export default ChatInput;