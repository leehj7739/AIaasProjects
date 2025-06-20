import React, { useState, useRef } from "react";
import { MdAutoAwesome, MdMenuBook } from "react-icons/md";
import { useNavigate } from "react-router-dom";
import { apiService } from "../services/api";
import { healthCheck } from "../services/api";
import FallbackImage from "./FallbackImage";

// FastAPI 서버 URL
const FASTAPI_BASE_URL = 'http://192.168.45.120:8000';

// 이미지 리사이즈 유틸리티
const imageResizeUtils = {
  // 이미지 리사이즈 함수
  resizeImage: (file, maxWidth = 1200, maxHeight = 1600, quality = 0.85) => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // 원본 이미지 크기
        const originalWidth = img.width;
        const originalHeight = img.height;
        
        // 비율 계산
        let newWidth = originalWidth;
        let newHeight = originalHeight;
        
        // 가로세로 비율 유지하면서 리사이즈
        if (originalWidth > maxWidth || originalHeight > maxHeight) {
          const ratio = Math.min(maxWidth / originalWidth, maxHeight / originalHeight);
          newWidth = Math.round(originalWidth * ratio);
          newHeight = Math.round(originalHeight * ratio);
        }
        
        // 캔버스 크기 설정
        canvas.width = newWidth;
        canvas.height = newHeight;
        
        // 이미지 그리기 (고품질 렌더링)
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, 0, 0, newWidth, newHeight);
        
        // JPEG로 변환
        canvas.toBlob(
          (blob) => {
            if (blob) {
              // 원본 파일명 유지하면서 리사이즈 정보 추가
              const originalName = file.name;
              const nameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.'));
              const extension = originalName.substring(originalName.lastIndexOf('.'));
              const resizedName = `${nameWithoutExt}_resized${extension}`;
              
              const resizedFile = new File([blob], resizedName, {
                type: 'image/jpeg',
                lastModified: Date.now()
              });
              
              console.log('🖼️ 이미지 리사이즈 완료:', {
                original: `${originalWidth}x${originalHeight} (${(file.size / 1024 / 1024).toFixed(2)}MB)`,
                resized: `${newWidth}x${newHeight} (${(resizedFile.size / 1024 / 1024).toFixed(2)}MB)`,
                compression: `${((1 - resizedFile.size / file.size) * 100).toFixed(1)}%`
              });
              
              resolve(resizedFile);
            } else {
              reject(new Error('이미지 리사이즈 실패'));
            }
          },
          'image/jpeg',
          quality
        );
      };
      
      img.onerror = () => reject(new Error('이미지 로드 실패'));
      img.src = URL.createObjectURL(file);
    });
  },
  
  // 이미지 크기 체크 함수
  checkImageSize: (file) => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const size = {
          width: img.width,
          height: img.height,
          fileSize: file.size,
          aspectRatio: img.width / img.height
        };
        resolve(size);
      };
      img.onerror = () => reject(new Error('이미지 크기 확인 실패'));
      img.src = URL.createObjectURL(file);
    });
  },
  
  // 리사이즈 필요 여부 확인
  needsResize: (width, height, maxWidth = 1200, maxHeight = 1600) => {
    return width > maxWidth || height > maxHeight;
  },
  
  // URL 이미지 다운로드 및 리사이징
  downloadAndResizeUrlImage: async (imageUrl, maxWidth = 1200, maxHeight = 1600, quality = 0.85) => {
    try {
      console.log('📥 URL 이미지 다운로드 시작:', imageUrl);
      
      // 이미지 다운로드 (CORS 우회를 위한 프록시 사용)
      let response;
      try {
        // 직접 다운로드 시도
        response = await fetch(imageUrl);
      } catch (corsError) {
        console.log('🔄 CORS 오류 발생, 프록시 사용 시도...');
        // CORS 오류 시 프록시 사용
        const proxyUrl = `https://cors-anywhere.herokuapp.com/${imageUrl}`;
        response = await fetch(proxyUrl, {
          headers: {
            'Origin': window.location.origin,
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
      }
      
      if (!response.ok) {
        throw new Error(`이미지 다운로드 실패: ${response.status}`);
      }
      
      const blob = await response.blob();
      const originalFile = new File([blob], 'url_image.jpg', { type: blob.type });
      
      console.log('📥 이미지 다운로드 완료:', {
        size: `${(blob.size / 1024 / 1024).toFixed(2)}MB`,
        type: blob.type
      });
      
      // 이미지 크기 체크
      const imageSize = await imageResizeUtils.checkImageSize(originalFile);
      console.log('📏 다운로드된 이미지 크기:', {
        width: imageSize.width,
        height: imageSize.height,
        fileSize: `${(imageSize.fileSize / 1024 / 1024).toFixed(2)}MB`,
        aspectRatio: imageSize.aspectRatio.toFixed(2)
      });
      
      // 리사이즈 필요 여부 확인
      if (imageResizeUtils.needsResize(imageSize.width, imageSize.height)) {
        console.log('🔄 URL 이미지 리사이즈 시작...');
        const resizedFile = await imageResizeUtils.resizeImage(originalFile, maxWidth, maxHeight, quality);
        
        // 리사이즈 정보 반환
        const resizeInfo = {
          original: {
            width: imageSize.width,
            height: imageSize.height,
            size: originalFile.size
          },
          processed: {
            width: Math.round(imageSize.width * Math.min(maxWidth / imageSize.width, maxHeight / imageSize.height)),
            height: Math.round(imageSize.height * Math.min(maxWidth / imageSize.width, maxHeight / imageSize.height)),
            size: resizedFile.size
          },
          compression: ((1 - resizedFile.size / originalFile.size) * 100).toFixed(1)
        };
        
        console.log('✅ URL 이미지 리사이즈 완료:', {
          original: `${imageSize.width}x${imageSize.height} (${(originalFile.size / 1024 / 1024).toFixed(2)}MB)`,
          resized: `${resizeInfo.processed.width}x${resizeInfo.processed.height} (${(resizedFile.size / 1024 / 1024).toFixed(2)}MB)`,
          compression: `${resizeInfo.compression}%`
        });
        
        return { file: resizedFile, resizeInfo, originalFile };
      } else {
        console.log('✅ URL 이미지 크기가 적절함, 리사이즈 생략');
        return { file: originalFile, resizeInfo: null, originalFile };
      }
      
    } catch (error) {
      console.error('❌ URL 이미지 처리 실패:', error);
      throw new Error(`URL 이미지 처리 실패: ${error.message}`);
    }
  }
};

export default function Ocr({ loading, setLoading, setSearchQuery }) {
  const [mode, setMode] = useState("image"); // 'image' or 'url'
  const [status, setStatus] = useState(null); // null | 'success' | 'error'
  const [errorMessage, setErrorMessage] = useState(""); // 에러 메시지
  const fileInputRef = useRef();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [ocrTitle, setOcrTitle] = useState("위버멘쉬"); // 실제 OCR 결과로 대체 필요
  
  // 이미지 관련 상태 추가
  const [originalImage, setOriginalImage] = useState(null); // 오리지널 이미지 (File 객체 또는 URL)
  const [ocrResultImage, setOcrResultImage] = useState(null); // 서버에서 받은 OCR 결과 이미지
  const [ocrData, setOcrData] = useState(null); // OCR 결과 데이터
  const [resizeInfo, setResizeInfo] = useState(null); // 리사이즈 정보

  // FastAPI 서버 헬스체크 함수
  const checkServerHealth = async () => {
    try {
      console.log('🔍 이미지 전송 전 서버 헬스체크 시작...');
      const health = await healthCheck.checkHealth();
      
      if (health.status === 'unhealthy') {
        throw new Error(`서버 상태 불량: ${health.error.message}`);
      }
      
      console.log('✅ 서버 헬스체크 성공:', health.responseTime);
      return true;
    } catch (error) {
      console.error('❌ 서버 헬스체크 실패:', error.message);
      throw new Error(`서버 연결 실패: ${error.message}`);
    }
  };

  // 실제 이미지 업로드 API 호출
  const handleImageUpload = async (file) => {
    try {
      setLoading(true);
      setStatus(null);
      setErrorMessage("");
      
      // 오리지널 이미지 저장
      setOriginalImage(file);
      
      // 이미지 크기 체크
      console.log('🔍 이미지 크기 확인 중...');
      const imageSize = await imageResizeUtils.checkImageSize(file);
      console.log('📏 이미지 크기:', {
        width: imageSize.width,
        height: imageSize.height,
        fileSize: `${(imageSize.fileSize / 1024 / 1024).toFixed(2)}MB`,
        aspectRatio: imageSize.aspectRatio.toFixed(2)
      });
      
      // 리사이즈 필요 여부 확인
      let processedFile = file;
      let resizeInfo = null;
      if (imageResizeUtils.needsResize(imageSize.width, imageSize.height)) {
        console.log('🔄 이미지 리사이즈 시작...');
        processedFile = await imageResizeUtils.resizeImage(file);
        console.log('✅ 리사이즈된 이미지로 업로드:', processedFile.name);
        
        // 리사이즈 정보 저장
        resizeInfo = {
          original: {
            width: imageSize.width,
            height: imageSize.height,
            size: file.size
          },
          processed: {
            width: Math.round(imageSize.width * Math.min(1200 / imageSize.width, 1600 / imageSize.height)),
            height: Math.round(imageSize.height * Math.min(1200 / imageSize.width, 1600 / imageSize.height)),
            size: processedFile.size
          },
          compression: ((1 - processedFile.size / file.size) * 100).toFixed(1)
        };
        setResizeInfo(resizeInfo);
      } else {
        console.log('✅ 이미지 크기가 적절함, 리사이즈 생략');
        setResizeInfo(null);
      }
      
      // 이미지 전송 전 서버 헬스체크
      await checkServerHealth();
      
      console.log('🚀 이미지 업로드 및 OCR+GPT 처리 시작...');
      const response = await apiService.uploadImage(processedFile);
      
      // FastAPI CombinedResponse 구조에 맞게 데이터 처리
      const { ocr_result, gpt_result, total_processing_time_ms } = response.data;
      
      console.log('📊 OCR 결과:', ocr_result);
      console.log('🤖 GPT 결과:', gpt_result);
      console.log('⏱️ 총 처리 시간:', total_processing_time_ms, 'ms');
      
      // OCR 결과 데이터 저장
      setOcrData(ocr_result);
      
      // OCR 결과 이미지 URL 설정 (서버에서 반환된 경우)
      if (ocr_result?.result_image_url) {
        // 상대 경로인 경우 FastAPI 서버 URL과 결합
        const imageUrl = ocr_result.result_image_url.startsWith('http') 
          ? ocr_result.result_image_url 
          : `${FASTAPI_BASE_URL}${ocr_result.result_image_url}`;
        setOcrResultImage(imageUrl);
      } else if (ocr_result?.annotated_image_url) {
        const imageUrl = ocr_result.annotated_image_url.startsWith('http') 
          ? ocr_result.annotated_image_url 
          : `${FASTAPI_BASE_URL}${ocr_result.annotated_image_url}`;
        setOcrResultImage(imageUrl);
      } else {
        // 서버에서 이미지 URL을 반환하지 않는 경우, 오리지널 이미지를 OCR 결과로 사용
        setOcrResultImage(URL.createObjectURL(file));
      }
      
      // GPT 결과에서 추출된 책 제목 사용
      const extractedTitle = gpt_result?.gpt_response || 
                           gpt_result?.extracted_title || 
                           gpt_result?.book_title || 
                           ocr_result?.extracted_text?.substring(0, 50) + '...' || 
                           "제목을 찾을 수 없습니다";
      
      setOcrTitle(extractedTitle);
      
      setStatus("success");
      console.log("✅ OCR+GPT 처리 완료:", {
        title: extractedTitle,
        ocrText: ocr_result?.extracted_text,
        confidence: ocr_result?.confidence,
        processingTime: total_processing_time_ms,
        originalImage: file.name,
        processedImage: processedFile.name,
        originalSize: `${(file.size / 1024 / 1024).toFixed(2)}MB`,
        processedSize: `${(processedFile.size / 1024 / 1024).toFixed(2)}MB`,
        ocrResultImage: ocr_result?.result_image_url ? `${FASTAPI_BASE_URL}${ocr_result.result_image_url}` : '오리지널 이미지 사용',
        gptResponse: gpt_result?.gpt_response,
        tokensUsed: gpt_result?.tokens_used,
        gptModel: gpt_result?.gpt_model
      });
      
    } catch (error) {
      console.error("이미지 업로드 에러:", error);
      setStatus("error");
      setErrorMessage(error.message || "이미지 업로드에 실패했습니다.");
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
      
      // 오리지널 이미지 URL 저장
      setOriginalImage(search);
      
      // URL 이미지 다운로드 및 리사이징
      console.log('📥 URL 이미지 처리 시작...');
      const { file: processedFile, resizeInfo: urlResizeInfo, originalFile } = await imageResizeUtils.downloadAndResizeUrlImage(search);
      
      // 리사이즈 정보 저장
      setResizeInfo(urlResizeInfo);
      
      // URL 전송 전 서버 헬스체크
      await checkServerHealth();
      
      console.log('🚀 URL 처리 및 OCR+GPT 처리 시작...');
      const response = await apiService.uploadImage(processedFile);
      
      // FastAPI CombinedResponse 구조에 맞게 데이터 처리
      const { ocr_result, gpt_result, total_processing_time_ms } = response.data;
      
      console.log('📊 OCR 결과:', ocr_result);
      console.log('🤖 GPT 결과:', gpt_result);
      console.log('⏱️ 총 처리 시간:', total_processing_time_ms, 'ms');
      
      // OCR 결과 데이터 저장
      setOcrData(ocr_result);
      
      // OCR 결과 이미지 URL 설정 (서버에서 반환된 경우)
      if (ocr_result?.result_image_url) {
        // 상대 경로인 경우 FastAPI 서버 URL과 결합
        const imageUrl = ocr_result.result_image_url.startsWith('http') 
          ? ocr_result.result_image_url 
          : `${FASTAPI_BASE_URL}${ocr_result.result_image_url}`;
        setOcrResultImage(imageUrl);
      } else if (ocr_result?.annotated_image_url) {
        const imageUrl = ocr_result.annotated_image_url.startsWith('http') 
          ? ocr_result.annotated_image_url 
          : `${FASTAPI_BASE_URL}${ocr_result.annotated_image_url}`;
        setOcrResultImage(imageUrl);
      } else {
        // 서버에서 이미지 URL을 반환하지 않는 경우, 오리지널 URL을 OCR 결과로 사용
        setOcrResultImage(search);
      }
      
      // GPT 결과에서 추출된 책 제목 사용
      const extractedTitle = gpt_result?.gpt_response || 
                           gpt_result?.extracted_title || 
                           gpt_result?.book_title || 
                           ocr_result?.extracted_text?.substring(0, 50) + '...' || 
                           "제목을 찾을 수 없습니다";
      
      setOcrTitle(extractedTitle);
      
      setStatus("success");
      console.log("✅ OCR+GPT 처리 완료:", {
        title: extractedTitle,
        ocrText: ocr_result?.extracted_text,
        confidence: ocr_result?.confidence,
        processingTime: total_processing_time_ms,
        originalImage: search,
        processedImage: processedFile.name,
        originalSize: urlResizeInfo ? `${(originalFile.size / 1024 / 1024).toFixed(2)}MB` : `${(processedFile.size / 1024 / 1024).toFixed(2)}MB`,
        processedSize: `${(processedFile.size / 1024 / 1024).toFixed(2)}MB`,
        ocrResultImage: ocr_result?.result_image_url ? `${FASTAPI_BASE_URL}${ocr_result.result_image_url}` : '오리지널 URL 사용',
        gptResponse: gpt_result?.gpt_response,
        tokensUsed: gpt_result?.tokens_used,
        gptModel: gpt_result?.gpt_model
      });
      
    } catch (error) {
      console.error("URL 업로드 에러:", error);
      setStatus("error");
      setErrorMessage(error.message || "URL 처리에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 파일 선택창 열기
  const handleBrowseClick = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  // 파일 선택 시 처리
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleImageUpload(file);
    }
  };

  const handleOk = () => {
    if (ocrTitle) {
      setSearchQuery(ocrTitle);
      navigate("/info");
    }
    resetStatus();
  };

  const resetStatus = () => {
    setStatus(null);
    setErrorMessage("");
    // 이미지 상태 초기화
    setOriginalImage(null);
    setOcrResultImage(null);
    setOcrData(null);
    setResizeInfo(null);
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
          {/* URL 업로드 버튼 */}
          <button 
            onClick={handleUrlUpload}
            disabled={loading || !search.trim()}
            className="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '처리 중...' : 'URL 처리'}
          </button>
          {/* 업로드 결과 메시지 */}
          {!loading && status === "success" && (
            <div className="mt-4 text-green-600 dark:text-green-400 flex items-center gap-1">
              <span>✅</span> 처리 성공!
            </div>
          )}
          {!loading && status === "error" && (
            <div className="mt-4 text-red-600 dark:text-red-400 flex items-center gap-1">
              <span>❌</span> {errorMessage || "처리 실패. 다시 시도해 주세요."}
            </div>
          )}
        </div>
      )}

      {/* 업로드 성공시 전체 오버레이 */}
      {status === "success" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 animate-fadein">
          <div className="bg-gradient-to-br from-white via-violet-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl p-8 max-w-md w-full text-center relative border-2 border-violet-200 dark:border-gray-700 animate-fadein-up">
            {/* 좌상단 닫기 버튼 */}
            <button
              className="absolute top-4 left-4 text-gray-400 hover:text-violet-600 text-2xl transition-colors"
              onClick={resetStatus}
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
                {originalImage ? (
                  typeof originalImage === 'string' ? (
                    // URL인 경우
                    <img 
                      src={originalImage} 
                      alt="오리지널 이미지" 
                      className="w-24 h-32 object-cover rounded-xl shadow-lg transition-transform duration-200 hover:scale-110"
                      onError={(e) => {
                        e.target.src = "/dummy-image.png";
                        console.warn("오리지널 이미지 로드 실패, 더미 이미지 사용");
                      }}
                    />
                  ) : (
                    // File 객체인 경우
                    <img 
                      src={URL.createObjectURL(originalImage)} 
                      alt="오리지널 이미지" 
                      className="w-24 h-32 object-cover rounded-xl shadow-lg transition-transform duration-200 hover:scale-110"
                    />
                  )
                ) : (
                  <FallbackImage src="/dummy-image.png" alt="오리지널 이미지" className="w-24 h-32 object-cover rounded-xl shadow-lg transition-transform duration-200 hover:scale-110" />
                )}
                <span className="text-xs mt-2 text-gray-500">오리지널</span>
              </div>
              {/* OCR 박싱 이미지 */}
              <div className="flex flex-col items-center group">
                {ocrResultImage ? (
                  <img 
                    src={ocrResultImage} 
                    alt="OCR 결과 이미지" 
                    className="w-24 h-32 object-cover rounded-xl shadow-lg border-4 border-blue-400 transition-transform duration-200 hover:scale-110"
                    onError={(e) => {
                      e.target.src = "/dummy-image.png";
                      console.warn("OCR 결과 이미지 로드 실패, 더미 이미지 사용");
                    }}
                  />
                ) : (
                  <FallbackImage src="/dummy-image.png" alt="OCR 결과 이미지" className="w-24 h-32 object-cover rounded-xl shadow-lg border-4 border-blue-400 transition-transform duration-200 hover:scale-110" />
                )}
                <span className="text-xs mt-2 text-blue-500 font-bold">OCR 결과</span>
              </div>
            </div>
            <div className="mb-6 text-lg text-gray-800 dark:text-gray-100 flex items-center justify-center gap-2">
              <MdMenuBook className="text-violet-600 dark:text-violet-300" />
              도서 제목 : <span className="font-bold text-blue-700 dark:text-blue-300">{ocrTitle}</span>
            </div>
            
            {/* 리사이즈 정보 표시 */}
            {resizeInfo && (
              <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
                <div className="text-sm text-blue-700 dark:text-blue-300 font-semibold mb-2">
                  🖼️ 이미지 최적화 완료
                </div>
                <div className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
                  <div>원본: {resizeInfo.original.width}×{resizeInfo.original.height} ({(resizeInfo.original.size / 1024 / 1024).toFixed(2)}MB)</div>
                  <div>최적화: {resizeInfo.processed.width}×{resizeInfo.processed.height} ({(resizeInfo.processed.size / 1024 / 1024).toFixed(2)}MB)</div>
                  <div>압축률: {resizeInfo.compression}%</div>
                </div>
              </div>
            )}

            <div className="flex justify-center gap-6 mt-2">
              <button className="px-8 py-2 rounded-lg bg-gradient-to-r from-green-400 to-blue-500 text-white font-bold text-base shadow hover:from-green-500 hover:to-blue-600 transition-all duration-200 scale-100 hover:scale-105" onClick={handleOk}>ok</button>
              <button className="px-8 py-2 rounded-lg bg-gradient-to-r from-gray-300 to-gray-400 text-gray-800 font-bold text-base shadow hover:from-gray-400 hover:to-gray-500 transition-all duration-200 scale-100 hover:scale-105" onClick={resetStatus}>no</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 