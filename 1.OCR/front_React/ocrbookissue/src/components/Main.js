import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import FallbackImage from "./FallbackImage";
import { apiService } from "../services/api";
import { 
  HiOutlineCamera, 
  HiOutlineMagnifyingGlass, 
  HiOutlineBookOpen, 
  HiOutlineBuildingLibrary,
  HiOutlineClock,
  HiOutlineSparkles,
  HiOutlineBolt,
  HiOutlineShieldCheck
} from "react-icons/hi2";

export default function Main() {
  const navigate = useNavigate();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // 추천도서 API 호출
  useEffect(() => {
    const fetchRecommendedBooks = async () => {
      try {
        setLoading(true);
        const recommendedBooks = await apiService.getRecommendedBooks();
        setBooks(recommendedBooks);
      } catch (error) {
        console.error("추천도서 로딩 실패:", error);
        // 에러 시 기본 더미 데이터 사용 (실제 API 응답 구조에 맞춤)
        setBooks([
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
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendedBooks();
  }, []);

  // 주요 기능들
  const features = [
    {
      icon: <HiOutlineCamera className="w-8 h-8" />,
      title: "OCR 도서 검색",
      desc: "책 표지를 촬영하면 자동으로 도서 정보를 인식하고 검색합니다",
      color: "from-blue-500 to-purple-600",
      path: "/ocr"
    },
    {
      icon: <HiOutlineMagnifyingGlass className="w-8 h-8" />,
      title: "도서 정보 검색",
      desc: "제목, ISBN, 키워드로 원하는 도서를 빠르게 찾아보세요",
      color: "from-green-500 to-teal-600",
      path: "/info"
    },
    {
      icon: <HiOutlineBuildingLibrary className="w-8 h-8" />,
      title: "도서관 위치 검색",
      desc: "주변 도서관과 대여 가능 여부를 한눈에 확인하세요",
      color: "from-orange-500 to-red-600",
      path: "/library"
    },
    {
      icon: <HiOutlineClock className="w-8 h-8" />,
      title: "검색 히스토리",
      desc: "이전에 검색한 내용을 쉽게 다시 찾아볼 수 있습니다",
      color: "from-purple-500 to-pink-600",
      path: "/history"
    }
  ];

  // 앱의 장점들
  const benefits = [
    {
      icon: <HiOutlineSparkles className="w-6 h-6" />,
      title: "정확한 인식",
      desc: "최신 AI 기술로 책 표지를 정확하게 인식합니다"
    },
    {
      icon: <HiOutlineBolt className="w-6 h-6" />,
      title: "빠른 검색",
      desc: "실시간으로 도서 정보와 대여 가능 여부를 확인합니다"
    },
    {
      icon: <HiOutlineShieldCheck className="w-6 h-6" />,
      title: "안전한 서비스",
      desc: "개인정보 보호와 데이터 보안을 최우선으로 합니다"
    }
  ];

  return (
    <main className="flex-1 flex flex-col bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 overflow-x-hidden">
      {/* 헤로 섹션 */}
      <section className="px-4 py-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
              📚 <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                OCR 도서 검색
              </span>
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
              책 표지를 촬영하면 자동으로 도서 정보를 찾아주는<br />
              스마트한 도서 검색 서비스입니다
            </p>
          </div>
          
          {/* 빠른 시작 버튼 */}
          <div className="flex flex-col sm:flex-row gap-3 mb-8">
            <button 
              onClick={() => navigate('/ocr')}
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              📸 OCR 검색 시작
            </button>
            <button 
              onClick={() => navigate('/info')}
              className="flex-1 bg-gradient-to-r from-green-600 to-teal-600 text-white py-3 px-6 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              🔍 도서 검색
            </button>
          </div>
        </div>
      </section>

      {/* 주요 기능 섹션 */}
      <section className="px-4 py-6">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
          주요 기능
        </h2>
        <div className="grid grid-cols-1 gap-4 max-w-md mx-auto">
          {features.map((feature, index) => (
            <div 
              key={index}
              onClick={() => navigate(feature.path)}
              className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 cursor-pointer border border-gray-100 dark:border-gray-700"
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg bg-gradient-to-r ${feature.color} text-white flex-shrink-0`}>
                  {feature.icon}
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {feature.desc}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 앱의 장점 섹션 */}
      <section className="px-4 py-6">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
          왜 OCR 도서 검색인가요?
        </h2>
        <div className="grid grid-cols-1 gap-4 max-w-md mx-auto">
          {benefits.map((benefit, index) => (
            <div key={index} className="bg-white/50 dark:bg-gray-800/50 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg text-blue-600 dark:text-blue-300">
                  {benefit.icon}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-sm">
                    {benefit.title}
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-300">
                    {benefit.desc}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 추천 도서 섹션 */}
      <section className="px-4 py-6">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
          📖 추천 도서
        </h2>
        {loading ? (
          <div className="max-w-md mx-auto text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
            <div className="text-gray-600 dark:text-gray-400">
              추천 도서를 불러오는 중...
            </div>
          </div>
        ) : (
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
                  <div className="flex-1">
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
                    <a
                      href={book.bookDtlUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full block bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-4 rounded-lg font-bold text-sm hover:shadow-lg transition-all duration-300 text-center"
                    >
                      상세 정보 보기
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 하단 CTA 섹션 */}
      <section className="px-4 py-8 text-center">
        <div className="max-w-md mx-auto">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
            지금 바로 시작해보세요!
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            책 표지를 촬영하고 원하는 도서를 찾아보세요
          </p>
          <button 
            onClick={() => navigate('/ocr')}
            className="bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 px-8 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
          >
            🚀 OCR 검색 시작하기
          </button>
        </div>
      </section>
    </main>
  );
} 