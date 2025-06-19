import React, { useState, useRef } from "react";
import { MdAutoAwesome, MdMenuBook } from "react-icons/md";
import { useNavigate } from "react-router-dom";
import { apiService } from "../services/api";
import FallbackImage from "./FallbackImage";

export default function Ocr({ loading, setLoading, setSearchQuery }) {
  const [mode, setMode] = useState("image"); // 'image' or 'url'
  const [status, setStatus] = useState(null); // null | 'success' | 'error'
  const [errorMessage, setErrorMessage] = useState(""); // 에러 메시지
  const fileInputRef = useRef();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [ocrTitle, setOcrTitle] = useState("위버멘쉬"); // 실제 OCR 결과로 대체 필요

  // 실제 이미지 업로드 API 호출
  const handleImageUpload = async (file) => {
    try {
      setLoading(true);
      setStatus(null);
      setErrorMessage("");
      
      const response = await apiService.uploadImage(file);
      
      // API 응답에서 OCR 결과 추출
      const { title, confidence, text } = response.data;
      setOcrTitle(title || "제목을 찾을 수 없습니다");
      
      setStatus("success");
      console.log("OCR 결과:", response.data);
      
    } catch (error) {
      console.error("이미지 업로드 에러:", error);
      setStatus("error");
      setErrorMessage(error.response?.data?.message || "이미지 업로드에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 실제 URL 업로드 API 호출
  const handleUrlUpload = async () => {
    if (!search.trim()) {
      setErrorMessage("URL을 입력해주세요.");
      return;
    }

    try {
      setLoading(true);
      setStatus(null);
      setErrorMessage("");
      
      const response = await apiService.processUrl(search);
      
      // API 응답에서 OCR 결과 추출
      const { title, confidence, text } = response.data;
      setOcrTitle(title || "제목을 찾을 수 없습니다");
      
      setStatus("success");
      console.log("OCR 결과:", response.data);
      
    } catch (error) {
      console.error("URL 업로드 에러:", error);
      setStatus("error");
      setErrorMessage(error.response?.data?.message || "URL 처리에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 테스트용 로딩+성공/실패 시뮬레이션
  const handleTest = (result) => {
    setLoading(true);
    setStatus(null);
    setTimeout(() => {
      setLoading(false);
      setStatus(result);
    }, 1000);
  };

  // 파일 선택창 열기
  const handleBrowseClick = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  // 파일 선택 시 처리
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // 파일 크기 체크 (30MB)
      if (file.size > 30 * 1024 * 1024) {
        setErrorMessage("파일 크기는 30MB 이하여야 합니다.");
        return;
      }
      
      // 파일 타입 체크
      if (!file.type.startsWith('image/')) {
        setErrorMessage("이미지 파일만 업로드 가능합니다.");
        return;
      }
      
      handleImageUpload(file);
    }
  };

  // URL 업로드 테스트용 함수 추가
  const handleUrlTest = (result) => {
    setLoading(true);
    setStatus(null);
    setTimeout(() => {
      setLoading(false);
      setStatus(result);
    }, 1000);
  };

  // ok 버튼 클릭 핸들러
  const handleOk = () => {
    navigate(`/info?query=${encodeURIComponent(ocrTitle)}`);
    setStatus(null);
  };

  return (
    <div className="relative flex flex-col items-center w-full min-h-full p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {/* 업로드 방식 토글 */}
      <div className={`flex gap-2 mb-4 w-full max-w-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 p-1 transition-colors duration-200 ${loading ? "pointer-events-none opacity-60" : ""}` }>
        <button
          className={`flex-1 py-2 rounded-md font-bold transition-colors duration-200 ${mode === "image" ? "bg-blue-600 text-white shadow" : "bg-transparent text-gray-700 dark:text-gray-200"}`}
          onClick={() => setMode("image")}
        >
          이미지 업로드
        </button>
        <button
          className={`flex-1 py-2 rounded-md font-bold transition-colors duration-200 ${mode === "url" ? "bg-blue-600 text-white shadow" : "bg-transparent text-gray-700 dark:text-gray-200"}`}
          onClick={() => setMode("url")}
        >
          URL 업로드
        </button>
      </div>

      {/* 선택된 UI만 표시 */}
      {mode === "image" ? (
        <div className={`relative w-full max-w-xs border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 flex flex-col items-center mb-6 bg-white dark:bg-gray-800 ${loading ? "pointer-events-none opacity-60" : ""}` }>
          <div className="text-4xl text-gray-400 mb-2">⬆️</div>
          <div className="text-gray-500 dark:text-gray-300 text-center mb-2">
            <span className="font-semibold">Click to upload</span> or drag and drop<br/>
            <span className="text-xs">Max. File Size: 30MB</span>
          </div>
          {/* 숨겨진 파일 input */}
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            type="button"
            onClick={handleBrowseClick}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
          >
            Browse File
          </button>
          {/* 업로드 결과 메시지 */}
          {!loading && status === "success" && (
            <div className="mt-4 text-green-600 dark:text-green-400 flex items-center gap-1">
              <span>✅</span> 업로드 성공!
            </div>
          )}
          {!loading && status === "error" && (
            <div className="mt-4 text-red-600 dark:text-red-400 flex items-center gap-1">
              <span>❌</span> {errorMessage || "업로드 실패. 다시 시도해 주세요."}
            </div>
          )}
        </div>
      ) : (
        <div className={`relative w-full max-w-xs mb-4 ${loading ? "pointer-events-none opacity-60" : ""}` }>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-200 mb-1">URL 이미지 전송</label>
          <input 
            type="text" 
            className="w-full rounded px-2 py-1 border border-gray-300 dark:border-gray-600 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" 
            placeholder="이미지 URL을 입력하세요"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {/* 업로드 결과 메시지 */}
          {!loading && status === "success" && (
            <div className="mt-4 text-green-600 dark:text-green-400 flex items-center gap-1">
              <span>✅</span> 업로드 성공!
            </div>
          )}
          {!loading && status === "error" && (
            <div className="mt-4 text-red-600 dark:text-red-400 flex items-center gap-1">
              <span>❌</span> {errorMessage || "업로드 실패. 다시 시도해 주세요."}
            </div>
          )}
          {/* URL 업로드 테스트용 버튼 */}
          <div className="flex gap-2 mt-4 w-full">
            <button onClick={() => handleUrlTest("success")}
              className="flex-1 py-2 rounded bg-green-500 text-white font-bold hover:bg-green-600 transition-colors">성공 테스트</button>
            <button onClick={() => handleUrlTest("error")}
              className="flex-1 py-2 rounded bg-red-500 text-white font-bold hover:bg-red-600 transition-colors">실패 테스트</button>
          </div>
        </div>
      )}

      <button 
        className={`w-full max-w-xs py-3 bg-blue-500 text-white rounded font-bold text-base hover:bg-blue-600 ${loading ? "pointer-events-none opacity-60" : ""}`}
        onClick={mode === "image" ? () => fileInputRef.current?.click() : handleUrlUpload}
      >
        {mode === "image" ? "이미지 업로드" : "URL 업로드"}
      </button>

      {/* 테스트용 버튼: 이미지 모드에서만 표시 */}
      {mode === "image" && (
        <div className={`flex gap-2 mt-4 w-full max-w-xs ${loading ? "pointer-events-none opacity-60" : ""}`}>
          <button onClick={() => handleTest("success")}
            className="flex-1 py-2 rounded bg-green-500 text-white font-bold hover:bg-green-600 transition-colors">성공 테스트</button>
          <button onClick={() => handleTest("error")}
            className="flex-1 py-2 rounded bg-red-500 text-white font-bold hover:bg-red-600 transition-colors">실패 테스트</button>
        </div>
      )}

      {/* 업로드 성공시 전체 오버레이 */}
      {status === "success" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 animate-fadein">
          <div className="bg-gradient-to-br from-white via-violet-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl p-8 max-w-md w-full text-center relative border-2 border-violet-200 dark:border-gray-700 animate-fadein-up">
            {/* 좌상단 닫기 버튼 */}
            <button
              className="absolute top-4 left-4 text-gray-400 hover:text-violet-600 text-2xl transition-colors"
              onClick={() => setStatus(null)}
              aria-label="닫기"
            >
              ×
            </button>
            <div className="text-2xl font-extrabold mb-4 text-violet-700 dark:text-violet-300 flex items-center justify-center gap-2">
              <MdAutoAwesome className="text-3xl align-middle" /> OCR 결과
            </div>
            <div className="flex justify-center items-end gap-8 mb-6">
              {/* 오리지널 이미지 */}
              <div className="flex flex-col items-center group">
                <FallbackImage src="/dummy-image.png" alt="오리지널 이미지" className="w-24 h-32 object-cover rounded-xl shadow-lg transition-transform duration-200 hover:scale-110" />
                <span className="text-xs mt-2 text-gray-500">오리지널</span>
              </div>
              {/* OCR 박싱 이미지 */}
              <div className="flex flex-col items-center group">
                <FallbackImage src="/dummy-image.png" alt="OCR 결과 이미지" className="w-24 h-32 object-cover rounded-xl shadow-lg border-4 border-blue-400 transition-transform duration-200 hover:scale-110" />
                <span className="text-xs mt-2 text-blue-500 font-bold">OCR 결과</span>
              </div>
            </div>
            <div className="mb-6 text-lg text-gray-800 dark:text-gray-100 flex items-center justify-center gap-2">
              <MdMenuBook className="text-violet-600 dark:text-violet-300" />
              도서 제목 : <span className="font-bold text-blue-700 dark:text-blue-300">{ocrTitle}</span>
            </div>
            <div className="flex justify-center gap-6 mt-2">
              <button className="px-8 py-2 rounded-lg bg-gradient-to-r from-green-400 to-blue-500 text-white font-bold text-base shadow hover:from-green-500 hover:to-blue-600 transition-all duration-200 scale-100 hover:scale-105" onClick={handleOk}>ok</button>
              <button className="px-8 py-2 rounded-lg bg-gradient-to-r from-gray-300 to-gray-400 text-gray-800 font-bold text-base shadow hover:from-gray-400 hover:to-gray-500 transition-all duration-200 scale-100 hover:scale-105" onClick={() => setStatus(null)}>no</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 