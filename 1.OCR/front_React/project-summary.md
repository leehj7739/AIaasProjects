# OCRBookIssue 프로젝트 상세 문서

## 📚 프로젝트 개요

- **목적**: 도서관 및 도서 정보를 쉽고 빠르게 검색하고, OCR(이미지 문자 인식) 기능을 통해 도서 정보를 자동으로 추출하는 웹 서비스
- **주요 기술**: React 18, Tailwind CSS 3.x, React Router, Axios, CRACO, XML 파싱(xml2js), 환경 변수 관리, CORS 우회, 이미지 Fallback, 모바일 최적화 등

---

## 🏗️ 프로젝트 구조

```
front_React/
  └─ ocrbookissue/
      ├─ public/
      │   ├─ index.html
      │   ├─ dummy-image.png
      │   └─ (기타 정적 파일)
      ├─ src/
      │   ├─ components/
      │   │   ├─ FallbackImage.js
      │   │   ├─ Footer.js
      │   │   ├─ Header.js
      │   │   ├─ Info.js
      │   │   ├─ Library.js
      │   │   ├─ Main.js
      │   │   ├─ Ocr.js
      │   │   └─ Price.js
      │   ├─ services/
      │   │   └─ api.js
      │   ├─ App.js
      │   └─ index.js
      ├─ craco.config.js
      ├─ package.json
      └─ tailwind.config.js
```

---

## ✨ 주요 기능

### 1. **도서관 정보 검색**
- 전국 도서관 실시간 검색(지역명, 도서관명, 주소, 전화번호 등)
- 지역별/전체 검색, 페이지네이션(20개씩 추가 로딩)
- ISBN 기반 도서관 소장 정보 검색(병렬 API 호출, 빠른 응답)
- 도서관 상세 정보(운영시간, 도서 수, 홈페이지 링크 등)
- 검색 결과 없음/로딩/에러 메시지 처리

### 2. **도서 정보 검색**
- ISBN/제목 기반 도서 검색(실시간 API 연동)
- ISBN 정규식 검증 및 분기 처리
- 도서 상세 정보(저자, 출판사, 출간연도, 표지, 대출 통계 등)
- XML 응답 파싱(xml2js) → JSON 변환

### 3. **OCR(이미지 문자 인식)**
- 이미지 업로드/URL 업로드 토글
- 업로드 성공/실패 메시지, 로딩 스피너 오버레이
- OCR 결과 도서 정보 자동 추출

### 4. **UI/UX**
- 헤더/푸터 고정, 다크모드 토글, 반응형 레이아웃
- Tailwind CSS 기반 모던 디자인
- 도서관 지역명 색상 구분, 홈페이지 링크 아이콘/말줄임표 처리
- 최상단 이동 플로팅 버튼(실제 스크롤 컨테이너 타겟팅)
- 모바일 환경에서 safe-area-inset, 동적 뷰포트 대응

### 5. **이미지 Fallback**
- 모든 이미지에 FallbackImage 컴포넌트 적용
- 이미지 로드 실패 시 더미 이미지(`dummy-image.png`) 자동 대체

---

## ⚡ 최적화 및 고급 기법

- **API 병렬 처리**: 도서관/도서 정보 검색 시 Promise.all로 병렬 호출, 빠른 응답
- **XML → JSON 파싱**: 공공 API의 XML 응답을 xml2js로 파싱, 구조화된 데이터 활용
- **환경 변수 관리**: API 키 등 민감 정보는 .env(환경 변수)로 분리
- **CORS 우회**: 프록시 설정, JSONP, 더미 데이터 폴백 등 다양한 우회 전략 적용
- **캐싱/로컬 상태 활용**: 검색 결과 캐싱, 페이지네이션 시 불필요한 API 호출 최소화
- **모바일 최적화**: safe-area-inset, 동적 뷰포트, CSS 리셋, 0.8px 보더 이슈 해결
- **코드 일관성**: 이미지 처리, 에러 처리, UI 컴포넌트화 등 반복 로직 글로벌화

---

## 🛠️ 사용된 주요 라이브러리 및 도구

- **React 18**
- **Tailwind CSS 3.x**
- **React Router**
- **Axios**
- **xml2js**
- **CRACO** (Webpack 5 polyfill 대응)
- **환경 변수(.env)**
- **기타: curl, CORS 프록시 등**

---

## 📝 기타 구현/개선 사항

- 더미 데이터와 실제 API 응답 구조 일치화
- 도서관/도서 검색 UI 분리 및 UX 개선
- 검색 결과 없음/로딩/에러 메시지 명확화
- 모든 이미지 경로 및 Fallback 처리 일원화
- 코드 리팩토링 및 불필요 파일/코드 정리

---

## 🚀 실행 및 개발 방법

1. 의존성 설치  
   ```bash
   npm install
   ```
2. 개발 서버 실행  
   ```bash
   npm start
   ```
3. 환경 변수(.env) 설정  
   - API 키 등 민감 정보는 `.env` 파일에 저장

---

## 📌 참고/특이사항

- 공공 API의 CORS, XML 응답 등으로 인해 프론트엔드에서 다양한 우회 및 파싱 전략을 적용
- 이미지 CDN 접근 제한(CORS) 이슈로, 표지 이미지는 직접 public 폴더에 저장하거나, hotlink 허용 이미지만 사용 권장
- 모든 이미지 처리에 FallbackImage 컴포넌트 사용

---

## 👨‍💻 주요 담당 기능/코드

- **공통 이미지 처리**: `src/components/FallbackImage.js`
- **도서관 검색**: `src/components/Library.js`
- **도서 검색/상세**: `src/components/Info.js`
- **OCR**: `src/components/Ocr.js`
- **API 연동/파싱**: `src/services/api.js`
- **메인/추천 도서**: `src/components/Main.js`
- **헤더/푸터/다크모드**: `src/components/Header.js`, `src/components/Footer.js`

---

## 💡 개선/확장 아이디어

- 사용자 인증 및 개인화 기능
- OCR 결과 자동 ISBN 추출 및 도서관 소장 정보 연동
- 검색 결과 즐겨찾기/공유 기능
- 서버사이드 프록시/캐싱 도입으로 CORS 및 속도 개선
- PWA(모바일 앱화), 접근성 강화 등

---

이 문서는 프로젝트의 전체 기능, 구조, 최적화 기법 등을 한눈에 볼 수 있도록 정리한 문서입니다. 