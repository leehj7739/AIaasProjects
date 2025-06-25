import React, { useState, useEffect } from "react";
import FallbackImage from "./FallbackImage";
import { apiService } from "../services/api";

// 추천도서 리스트 컴포넌트
const RecommendedBooksList = ({ books }) => (
  <div className="space-y-4 max-w-md mx-auto">
    {books.map((book) => (
      <div key={book.isbn13 || book.bookname} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 border border-gray-100 dark:border-gray-700">
        <div className="flex gap-4 items-center">
          <FallbackImage
            key={book.isbn13 || book.bookname}
            src={book.bookImageURL}
            alt="책 표지"
            className="w-24 h-32 object-cover rounded-lg shadow-md flex-shrink-0"
          />
          <div className="flex-1 flex flex-col justify-center min-h-[128px]">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-1 line-clamp-2">
              {book.bookname}
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-300 mb-1 line-clamp-1">
              {book.authors}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              {book.publisher} • {book.publication_year}
            </p>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-yellow-500">🏆</span>
              <span className="text-xs text-gray-600 dark:text-gray-300">
                대여 순위 {book.ranking}위
              </span>
              <span className="text-xs text-blue-600 dark:text-blue-400">
                • 대여 {book.loan_count}회
              </span>
            </div>
            {book.bookDtlUrl && (
              <a
                href={book.bookDtlUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full block bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-4 rounded-lg font-bold text-sm hover:shadow-lg transition-all duration-300 text-center"
              >
                상세 정보 보기
              </a>
            )}
          </div>
        </div>
      </div>
    ))}
  </div>
);

// 기본 더미 데이터
const defaultBooks = [
  {
    bookname: "괴물들 :숭배와 혐오, 우리 모두의 딜레마",
    authors: "클레어 데더러 지음 ;노지양 옮김",
    publisher: "을유문화사",
    publication_year: "2024",
    isbn13: "9788932475233",
    bookImageURL: "/dummy-image.png",
    loan_count: 38,
    ranking: 1
  },
  {
    bookname: "방구석 미술관 :가볍고 편하게 시작하는 유쾌한 교양 미술",
    authors: "조원재 지음",
    publisher: "백도씨",
    publication_year: "2018",
    isbn13: "9788968331862",
    bookImageURL: "/dummy-image.png",
    loan_count: 37,
    ranking: 2
  },
  {
    bookname: "모국어는 차라리 침묵 :목정원 산문",
    authors: "지은이: 목정원",
    publisher: "아침달",
    publication_year: "2021",
    isbn13: "9791189467302",
    bookImageURL: "/dummy-image.png",
    loan_count: 30,
    ranking: 3
  }
];

// 메인 추천도서 컴포넌트
const RecommendedBooks = () => {
  const [books, setBooks] = useState(defaultBooks);
  const [isUpdating, setIsUpdating] = useState(false);
  
  // 추천도서 API 호출
  useEffect(() => {
    const fetchRecommendedBooks = async () => {
      try {
        setIsUpdating(true);
        const recommendedBooks = await apiService.getRecommendedBooks();
        setBooks(recommendedBooks);
      } catch (error) {
        console.error("추천도서 로딩 실패:", error);
        // 에러 시 기본 더미 데이터 유지
      } finally {
        setIsUpdating(false);
      }
    };

    // 백그라운드에서 API 호출
    fetchRecommendedBooks();
  }, []);

  return (
    <section className="px-4 py-6">
      <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
        📖 추천 도서
        {isUpdating && (
          <span className="ml-2 inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></span>
        )}
      </h2>
      <RecommendedBooksList books={books} />
    </section>
  );
};

export default RecommendedBooks; 