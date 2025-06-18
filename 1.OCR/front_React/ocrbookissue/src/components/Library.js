import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

const dummyLibraries = [
  {
    name: "서울도서관",
    address: "서울특별시 중구 세종대로 110",
    homepage: "https://lib.seoul.go.kr/",
    phone: "02-2133-0300",
    region: "서울",
    hours: "월~금 09:00~21:00, 토~일 09:00~18:00",
    book: "위버멘쉬"
  },
  {
    name: "경기중앙도서관",
    address: "경기도 수원시 팔달구 효원로 293",
    homepage: "https://www.janganlib.or.kr/",
    phone: "031-228-4746",
    region: "경기",
    hours: "매일 09:00~22:00",
    book: "데미안"
  },
  {
    name: "부산시립도서관",
    address: "부산광역시 남구 유엔평화로 76",
    homepage: "https://www.busan.go.kr/library/",
    phone: "051-810-8200",
    region: "부산",
    hours: "화~일 09:00~18:00",
    book: "호밀밭의 파수꾼"
  },
  {
    name: "강남구립도서관",
    address: "서울특별시 강남구 테헤란로 410",
    homepage: "https://www.gangnamlib.or.kr/",
    phone: "02-1234-5678",
    region: "서울",
    hours: "월~금 09:00~20:00",
    book: "1984"
  },
  {
    name: "수원시립도서관",
    address: "경기도 수원시 장안구 경수대로 1111",
    homepage: "https://www.suwonlib.go.kr/",
    phone: "031-987-6543",
    region: "경기",
    hours: "매일 09:00~18:00",
    book: "위버멘쉬"
  },
  {
    name: "해운대도서관",
    address: "부산광역시 해운대구 해운대로 123",
    homepage: "https://www.haeundaelib.go.kr/",
    phone: "051-222-3333",
    region: "부산",
    hours: "화~일 09:00~19:00",
    book: "데미안"
  },
  {
    name: "노원구립도서관",
    address: "서울특별시 노원구 노해로 456",
    homepage: "https://www.nowonlib.or.kr/",
    phone: "02-555-6666",
    region: "서울",
    hours: "월~토 09:00~18:00",
    book: "호밀밭의 파수꾼"
  },
  {
    name: "안양시립도서관",
    address: "경기도 안양시 동안구 시민대로 789",
    homepage: "https://www.anyanglib.go.kr/",
    phone: "031-444-5555",
    region: "경기",
    hours: "매일 09:00~20:00",
    book: "1984"
  },
  {
    name: "동래도서관",
    address: "부산광역시 동래구 명륜로 321",
    homepage: "https://www.dongnaelib.go.kr/",
    phone: "051-777-8888",
    region: "부산",
    hours: "수~일 10:00~18:00",
    book: "위버멘쉬"
  },
  {
    name: "송파구립도서관",
    address: "서울특별시 송파구 올림픽로 135",
    homepage: "https://www.songpalib.or.kr/",
    phone: "02-888-9999",
    region: "서울",
    hours: "월~금 09:00~21:00",
    book: "데미안"
  },
  {
    name: "고양시립도서관",
    address: "경기도 고양시 일산동구 중앙로 100",
    homepage: "https://www.goyanglib.go.kr/",
    phone: "031-111-2222",
    region: "경기",
    hours: "매일 09:00~19:00",
    book: "호밀밭의 파수꾼"
  },
  {
    name: "사하구립도서관",
    address: "부산광역시 사하구 낙동대로 200",
    homepage: "https://www.sahalib.go.kr/",
    phone: "051-333-4444",
    region: "부산",
    hours: "월~토 09:00~18:00",
    book: "1984"
  },
  {
    name: "중구립도서관",
    address: "서울특별시 중구 을지로 50",
    homepage: "https://www.junggu.go.kr/lib/",
    phone: "02-777-8888",
    region: "서울",
    hours: "월~금 09:00~20:00",
    book: "위버멘쉬"
  },
  {
    name: "대구중앙도서관",
    address: "대구광역시 중구 공평로 10",
    homepage: "https://www.djlibrary.kr/",
    phone: "053-231-2000",
    region: "대구",
    hours: "월~금 09:00~20:00",
    book: "데미안"
  },
  {
    name: "인천광역시도서관",
    address: "인천광역시 남동구 예술로 149",
    homepage: "https://www.incheonlib.go.kr/",
    phone: "032-440-6666",
    region: "인천",
    hours: "매일 09:00~18:00",
    book: "1984"
  },
  {
    name: "광주광역시립도서관",
    address: "광주광역시 북구 설죽로 477",
    homepage: "https://www.gwangjulib.or.kr/",
    phone: "062-613-7750",
    region: "광주",
    hours: "화~일 09:00~19:00",
    book: "위버멘쉬"
  },
  {
    name: "대전시립도서관",
    address: "대전광역시 중구 중앙로 101",
    homepage: "https://www.daejeonlib.or.kr/",
    phone: "042-626-7000",
    region: "대전",
    hours: "월~금 09:00~20:00",
    book: "호밀밭의 파수꾼"
  },
  {
    name: "울산도서관",
    address: "울산광역시 남구 여천로 38",
    homepage: "https://www.ulsanlib.or.kr/",
    phone: "052-266-5670",
    region: "울산",
    hours: "매일 09:00~18:00",
    book: "데미안"
  },
  {
    name: "세종시립도서관",
    address: "세종특별자치시 한누리대로 215",
    homepage: "https://www.sejonglib.go.kr/",
    phone: "044-300-3900",
    region: "세종",
    hours: "월~금 09:00~19:00",
    book: "1984"
  },
  {
    name: "강원도립도서관",
    address: "강원도 춘천시 중앙로 1",
    homepage: "https://www.gwlib.or.kr/",
    phone: "033-258-2500",
    region: "강원",
    hours: "화~일 09:00~18:00",
    book: "위버멘쉬"
  },
  {
    name: "충북도서관",
    address: "충청북도 청주시 상당구 상당로 82",
    homepage: "https://www.cbplib.go.kr/",
    phone: "043-201-4151",
    region: "충북",
    hours: "월~금 09:00~20:00",
    book: "호밀밭의 파수꾼"
  },
  {
    name: "충남도서관",
    address: "충청남도 홍성군 홍북읍 충남대로 21",
    homepage: "https://www.cnl.go.kr/",
    phone: "041-635-8000",
    region: "충남",
    hours: "매일 09:00~18:00",
    book: "데미안"
  },
  {
    name: "전북도서관",
    address: "전라북도 전주시 완산구 서원로 137",
    homepage: "https://www.jblib.go.kr/",
    phone: "063-280-1000",
    region: "전북",
    hours: "월~금 09:00~20:00",
    book: "1984"
  },
  {
    name: "전남도서관",
    address: "전라남도 무안군 삼향읍 오룡길 20",
    homepage: "https://www.jnlib.or.kr/",
    phone: "061-286-5000",
    region: "전남",
    hours: "화~일 09:00~18:00",
    book: "위버멘쉬"
  },
  {
    name: "경북도서관",
    address: "경상북도 김천시 혁신8로 19",
    homepage: "https://www.gblib.kr/",
    phone: "054-650-3900",
    region: "경북",
    hours: "월~금 09:00~20:00",
    book: "호밀밭의 파수꾼"
  },
  {
    name: "경남도서관",
    address: "경상남도 창원시 의창구 중앙대로 300",
    homepage: "https://www.gnlib.go.kr/",
    phone: "055-254-4000",
    region: "경남",
    hours: "매일 09:00~18:00",
    book: "데미안"
  },
  {
    name: "제주도서관",
    address: "제주특별자치도 제주시 오남로 221",
    homepage: "https://www.jeju.lib.kr/",
    phone: "064-746-5101",
    region: "제주",
    hours: "월~금 09:00~20:00",
    book: "1984"
  }
];

export default function Library() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const bookParam = params.get("book");
    if (bookParam) {
      setQuery(bookParam);
      setSearch(bookParam);
    }
  }, [location.search]);

  // 통합 검색: 도서명, 도서관명, 지역 모두 포함
  const filtered = dummyLibraries.filter(lib =>
    [lib.book, lib.name, lib.region].some(field => field.includes(search))
  );

  return (
    <div className="flex flex-col items-center w-full min-h-0 flex-1 p-2 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {/* 통합 검색창 */}
      <form className="w-full max-w-xs mb-2 flex gap-2" onSubmit={e => { e.preventDefault(); setSearch(query); }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="도서명, 도서관명, 지역으로 검색"
          className="w-full rounded px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow"
        />
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded font-bold hover:bg-blue-700 transition">검색</button>
      </form>
      {/* 도서관 결과 리스트 */}
      <div className="w-full max-w-xs bg-white/60 dark:bg-gray-800/60 rounded-xl shadow-inner p-3 mt-2">
        {filtered.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">검색 결과가 없습니다.</div>
        ) : (
          <ul className="flex flex-col gap-4">
            {filtered.map((lib, idx) => (
              <li key={idx} className="bg-white dark:bg-gray-900 rounded-lg shadow p-4 flex flex-col gap-1 relative">
                <div className="flex items-center justify-between">
                  <div className="text-lg font-bold text-violet-700 dark:text-violet-300">{lib.name}</div>
                  <span className={`ml-2 px-2 py-1 rounded text-xs font-bold text-white
                    ${lib.region === '서울' ? 'bg-violet-500'
                    : lib.region === '대구' ? 'bg-red-500'
                    : lib.region === '부산' ? 'bg-green-600'
                    : lib.region === '인천' ? 'bg-sky-400'
                    : lib.region === '광주' ? 'bg-lime-500'
                    : lib.region === '대전' ? 'bg-yellow-400 text-gray-900'
                    : lib.region === '울산' ? 'bg-cyan-500'
                    : lib.region === '세종' ? 'bg-gray-500'
                    : lib.region === '경기' ? 'bg-blue-500'
                    : lib.region === '강원' ? 'bg-orange-400'
                    : lib.region === '충북' ? 'bg-indigo-700'
                    : lib.region === '충남' ? 'bg-amber-700'
                    : lib.region === '전북' ? 'bg-purple-300 text-gray-900'
                    : lib.region === '전남' ? 'bg-green-400'
                    : lib.region === '경북' ? 'bg-pink-400'
                    : lib.region === '경남' ? 'bg-teal-500'
                    : lib.region === '제주' ? 'bg-yellow-300 text-gray-900'
                    : 'bg-gray-400'}
                  `}>{lib.region}</span>
                </div>
                <div className="text-xs text-gray-700 dark:text-gray-300">주소: {lib.address}</div>
                <div className="text-xs text-gray-700 dark:text-gray-300">운영시간: {lib.hours}</div>
                <div className="text-xs text-gray-700 dark:text-gray-300">전화: {lib.phone}</div>
                <div className="text-xs text-gray-700 dark:text-gray-300 flex items-center gap-2">
                  홈페이지: <a href={lib.homepage} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-300 underline font-bold">바로가기</a>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
} 