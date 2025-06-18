import React from "react";
import { useNavigate } from "react-router-dom";

export default function Main() {
  const navigate = useNavigate();
  // 추천 도서 더미 데이터
  const books = [
    {
      img: "/book_image.jpg",
      title: "위버멘쉬",
      author: "프리드리히 니체",
      desc: "누구의 시선도 아닌, 내 의지대로 살겠다는 선언",
      rank: 123
    },
    {
      img: "/book_image.jpg",
      title: "데미안",
      author: "헤르만 헤세",
      desc: "자아를 찾아가는 성장의 여정",
      rank: 45
    },
    {
      img: "/book_image.jpg",
      title: "호밀밭의 파수꾼",
      author: "J.D. 샐린저",
      desc: "청춘의 방황과 진실에 대한 갈망",
      rank: 87
    },
    {
      img: "/book_image.jpg",
      title: "1984",
      author: "조지 오웰",
      desc: "감시와 통제, 자유에 대한 경고",
      rank: 12
    }
  ];

  return (
    <main className="flex-1 flex flex-col bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-2 overflow-x-hidden">
      {/* 추천 도서 카드 리스트 */}
      {books.map((book, idx) => (
        <div key={idx} className={`w-full max-w-2xl mx-auto rounded-xl shadow-lg flex flex-col md:flex-row items-center md:items-stretch p-4 gap-4 mb-6 ${idx % 2 === 0 ? 'bg-gray-50 dark:bg-gray-800' : 'bg-white dark:bg-gray-700'}`}>
          {/* 추천 도서 타이틀 (첫번째 카드만) */}
          {idx === 0 && (
            <div className="w-full md:w-1/3 mb-2 md:mb-0 flex flex-col items-center justify-center">
              <span className="inline-block text-lg md:text-2xl font-extrabold text-purple-700 dark:text-purple-300 tracking-wide drop-shadow mb-2">추천 도서</span>
            </div>
          )}
          {/* 도서 이미지 */}
          <img
            src={book.img}
            alt="책 표지"
            className="w-16 h-22 md:w-24 md:h-32 object-cover rounded-lg shadow-md mx-auto md:mx-0"
          />
          {/* 도서 정보 */}
          <div className="flex-1 flex flex-col justify-between h-full mt-2 md:mt-0">
            <div>
              <div className="text-base font-bold text-gray-900 dark:text-gray-100 mb-0.5">{book.title}</div>
              <div className="text-xs text-gray-700 dark:text-gray-300 mb-0.5">저자: {book.author}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{book.desc}</div>
            </div>
            <div className="flex items-center gap-1 mt-1">
              <span className="text-base">🏆</span>
              <span className="text-gray-700 dark:text-gray-200 text-xs">현재 대여 순위</span>
              <span className="text-teal-600 dark:text-teal-300 font-bold ml-0.5 text-xs">{book.rank} 위</span>
            </div>
            <div className="flex gap-2 mt-3 w-full">
              <button 
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg font-bold text-sm hover:bg-blue-700 transition"
                onClick={() => navigate(`/library?book=${encodeURIComponent(book.title)}`)}
              >
                대여하러 가기
              </button>
              <button 
                className="flex-1 py-2 bg-teal-500 text-white rounded-lg font-bold text-sm hover:bg-teal-600 transition"
                onClick={() => navigate(`/price?query=${encodeURIComponent(book.title)}`)}
              >
                가격비교
              </button>
            </div>
          </div>
        </div>
      ))}
    </main>
  );
} 