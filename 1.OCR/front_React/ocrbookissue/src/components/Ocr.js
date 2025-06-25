import React, { useState, useRef, useEffect } from "react";
import { MdAutoAwesome, MdMenuBook } from "react-icons/md";
import { useNavigate } from "react-router-dom";
import { apiService } from "../services/api";
import { healthCheck } from "../services/api";
import FallbackImage from "./FallbackImage";
import config from "../config/config";
import UploadModeToggle from "./UploadModeToggle";
import { v4 as uuidv4 } from 'uuid';

// FastAPI 서버 URL - config에서 가져오기
const FASTAPI_BASE_URL = config.FASTAPI_BASE_URL;

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

// URL 유효성 검사 함수
function isValidImageUrl(url) {
  try {
    new URL(url);
  } catch {
    return false;
  }
  return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(url);
}

// OCR 결과 저장 함수 (localStorage)
function saveOcrHistory(item) {
  // 필수값 유효성 검사
  if (!item || !item.id || !item.ocrResultImageUrl || !item.extractedText) {
    console.warn('[OCR 히스토리] 저장 실패: 필수값 누락', item);
    return;
  }
  const history = JSON.parse(localStorage.getItem('ocrHistory') || '[]');
  history.unshift(item);
  localStorage.setItem('ocrHistory', JSON.stringify(history.slice(0, 10)));
  console.log('[OCR 히스토리] 저장 성공:', item);
}

export default function Ocr(props) {
  const { loading, setLoading, setSearchQuery, viewMode, ocrData } = props;
  const [mode, setMode] = useState("image"); // 'image' or 'url'
  const [status, setStatus] = useState(null); // null | 'success' | 'error'
  const [search, setSearch] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [ocrDataState, setOcrData] = useState(null);
  const [ocrTitle, setOcrTitle] = useState("");
  const [ocrResultImage, setOcrResultImage] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);
  const [resizeInfo, setResizeInfo] = useState(null);
  const [showImageModal, setShowImageModal] = useState(false); // 이미지 확대 모달 (최상단에서 한 번만 선언)
  const [modalImage, setModalImage] = useState(null); // 확대 모달 이미지
  const fileInputRef = useRef();
  const navigate = useNavigate();

  // 페이지 진입 시 상태 초기화 (viewMode가 아닐 때만)
  useEffect(() => {
    if (!viewMode) {
      setMode("image");
      setStatus(null);
      setSearch("");
      setErrorMessage("");
      setOcrData(null);
      setOcrTitle("");
      setOcrResultImage(null);
      setOriginalImage(null);
      setResizeInfo(null);
      setShowImageModal(false);
      setModalImage(null);
      
      // 파일 입력 초기화
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [viewMode]);

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
      
      console.log('✅ OCR 처리 완료:', response.data);
      console.log('📊 OCR 결과 데이터:', response.data.ocr_result);
      console.log('🤖 GPT 결과 데이터:', response.data.gpt_result);
      
      const { ocr_result, gpt_result } = response.data;
      
      // OCR 결과 데이터 저장
      setOcrData(ocr_result);
      
      // OCR 결과 이미지 URL 설정 (서버에서 반환된 경우)
      setOcrResultImageWithFallback(ocr_result, search);
      
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
        processingTime: response.data.total_processing_time_ms,
        originalImage: file.name,
        processedImage: processedFile.name,
        originalSize: `${(file.size / 1024 / 1024).toFixed(2)}MB`,
        processedSize: `${(processedFile.size / 1024 / 1024).toFixed(2)}MB`,
        ocrResultImage: ocr_result?.result_image_url ? `${FASTAPI_BASE_URL}${ocr_result.result_image_url}` : ocr_result?.result_image_path ? `${FASTAPI_BASE_URL}/api/ocr/result/${ocr_result.result_image_path}` : '오리지널 이미지 사용',
        gptResponse: gpt_result?.gpt_response,
        tokensUsed: gpt_result?.tokens_used,
        gptModel: gpt_result?.gpt_model
      });
      
      // OCR 결과 저장
      const boundingBoxImageUrl = ocr_result?.result_image_url
        ? `${FASTAPI_BASE_URL}${ocr_result.result_image_url}`
        : ocr_result?.result_image_path
        ? `${FASTAPI_BASE_URL}/api/ocr/result/${ocr_result.result_image_path}`
        : null;
      let resizedImageUrl = null;
      if (processedFile instanceof File) {
        resizedImageUrl = URL.createObjectURL(processedFile);
      }
      saveOcrHistory({
        id: uuidv4(),
        ocrResultImageUrl: boundingBoxImageUrl,
        originalImageUrl: resizedImageUrl, // Blob URL
        extractedText: gpt_result?.gpt_response || ocr_result?.extracted_text,
        createdAt: new Date().toISOString()
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
      
      console.log('✅ OCR 처리 완료:', response.data);
      console.log('📊 OCR 결과 데이터:', response.data.ocr_result);
      console.log('🤖 GPT 결과 데이터:', response.data.gpt_result);
      
      const { ocr_result, gpt_result } = response.data;
      
      // OCR 결과 데이터 저장
      setOcrData(ocr_result);
      
      // OCR 결과 이미지 URL 설정 (서버에서 반환된 경우)
      setOcrResultImageWithFallback(ocr_result, search);
      
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
        processingTime: response.data.total_processing_time_ms,
        originalImage: search,
        processedImage: processedFile.name,
        originalSize: urlResizeInfo ? `${(originalFile.size / 1024 / 1024).toFixed(2)}MB` : `${(processedFile.size / 1024 / 1024).toFixed(2)}MB`,
        processedSize: `${(processedFile.size / 1024 / 1024).toFixed(2)}MB`,
        ocrResultImage: ocr_result?.result_image_url ? `${FASTAPI_BASE_URL}${ocr_result.result_image_url}` : ocr_result?.result_image_path ? `${FASTAPI_BASE_URL}/api/ocr/result/${ocr_result.result_image_path}` : '오리지널 URL 사용',
        gptResponse: gpt_result?.gpt_response,
        tokensUsed: gpt_result?.tokens_used,
        gptModel: gpt_result?.gpt_model
      });
      
      // OCR 결과 저장
      const boundingBoxImageUrl = ocr_result?.result_image_url
        ? `${FASTAPI_BASE_URL}${ocr_result.result_image_url}`
        : ocr_result?.result_image_path
        ? `${FASTAPI_BASE_URL}/api/ocr/result/${ocr_result.result_image_path}`
        : null;
      let resizedImageUrl = null;
      if (processedFile instanceof File) {
        resizedImageUrl = URL.createObjectURL(processedFile);
      }
      saveOcrHistory({
        id: uuidv4(),
        ocrResultImageUrl: boundingBoxImageUrl,
        originalImageUrl: resizedImageUrl, // Blob URL
        extractedText: gpt_result?.gpt_response || ocr_result?.extracted_text,
        createdAt: new Date().toISOString()
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
      if (file.size > 10 * 1024 * 1024) { // 10MB 제한
        setStatus("error");
        setErrorMessage("최대 파일 크기는 10MB입니다.");
        return;
      }
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
    setOcrTitle("");
    setOcrResultImage(null);
    setOriginalImage(null);
    setOcrData(null);
    setResizeInfo(null);
    setShowImageModal(false);
  };

  // 이미지 로드 실패 시 더미 이미지로 대체
  const handleImageError = (e) => {
    console.warn('❌ OCR 박싱 이미지 로드 실패, 더미 이미지 사용:', e.target.src);
    e.target.src = "/dummy-image.png";
  };

  // OCR 결과 이미지 URL 설정 함수
  const setOcrResultImageWithFallback = (ocr_result, fallbackImage) => {
    if (ocr_result?.result_image_url) {
      // 서버에서 제공하는 result_image_url 사용
      const boundingBoxImageUrl = `${FASTAPI_BASE_URL}${ocr_result.result_image_url}`;
      console.log('🔍 OCR 박싱 이미지 URL:', boundingBoxImageUrl);
      setOcrResultImage(boundingBoxImageUrl);
    } else if (ocr_result?.result_image_path) {
      // 기존 result_image_path도 지원 (하위 호환성)
      const boundingBoxImageUrl = `${FASTAPI_BASE_URL}/api/ocr/result/${ocr_result.result_image_path}`;
      console.log('🔍 OCR 박싱 이미지 URL (legacy):', boundingBoxImageUrl);
      setOcrResultImage(boundingBoxImageUrl);
    } else {
      console.log('⚠️ 서버에서 박싱 이미지 URL을 반환하지 않음, 오리지널 이미지 사용');
      setOcrResultImage(fallbackImage);
    }
  };

  // 뷰 모드: OCR 결과만 표시
  if (viewMode && ocrData) {
    const ocrImgUrl = ocrData.ocrResultImageUrl || ocrData.originalImageUrl;
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
        <div className="bg-gradient-to-br from-white via-violet-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl p-8 max-w-md w-full text-center relative border-2 border-violet-200 dark:border-gray-700 animate-fadein-up">
          {/* 좌상단 닫기 버튼 */}
          <button
            className="absolute top-4 left-4 text-gray-400 hover:text-violet-600 text-2xl transition-colors"
            onClick={() => window.history.back()}
            aria-label="닫기"
          >
            ×
          </button>
          <div className="text-2xl font-extrabold mb-4 text-violet-700 dark:text-violet-300 flex items-center justify-center gap-2">
            <span className="text-3xl align-middle">✨</span> OCR 도서제목 검출 결과
          </div>
          <div className="flex justify-center items-end gap-8 mb-6">
            {/* 오리지널 이미지 */}
            <div className="flex flex-col items-center group">
              <img src={ocrData.originalImageUrl} alt="오리지널 이미지" className="w-32 h-40 object-contain rounded-xl shadow-lg" />
              <span className="text-xs mt-2 text-gray-500 font-medium">오리지널 이미지</span>
            </div>
            {/* OCR 박싱 이미지 */}
            <div className="flex flex-col items-center group">
              <img
                src={ocrImgUrl}
                alt="OCR 결과 이미지"
                className="w-32 h-40 object-contain rounded-xl shadow-lg border-4 border-blue-400 cursor-pointer"
                onClick={() => setShowImageModal(true)}
              />
              <span className="text-xs mt-2 text-blue-500 font-medium">OCR 도서제목 검출 결과</span>
            </div>
          </div>
          <div className="mb-6 text-lg text-gray-800 dark:text-gray-100 flex items-center justify-center gap-2">
            <span className="font-bold text-blue-700 dark:text-blue-300">{ocrData.extractedText}</span>
          </div>
          <div className="text-xs text-gray-400 mb-2">{ocrData.createdAt && new Date(ocrData.createdAt).toLocaleString()}</div>
          {/* 확대 모달 */}
          {showImageModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 animate-fadein">
              <div className="bg-gradient-to-br from-white via-violet-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center relative border-2 border-violet-200 dark:border-gray-700 animate-fadein-up">
                <button
                  className="absolute top-4 left-4 text-gray-400 hover:text-violet-600 text-2xl transition-colors"
                  onClick={() => setShowImageModal(false)}
                  aria-label="닫기"
                >
                  ×
                </button>
                <div className="text-2xl font-extrabold mb-4 text-violet-700 dark:text-violet-300 flex items-center justify-center gap-2">
                  <span className="text-3xl align-middle">✨</span> OCR 도서제목 검출 결과
                </div>
                <div className="flex justify-center items-end gap-8 mb-6">
                  <div className="flex flex-col items-center group">
                    <img
                      src={ocrImgUrl}
                      alt="OCR 결과 이미지 (확대)"
                      className="max-w-[320px] max-h-[420px] object-contain rounded-xl shadow-lg border-4 border-blue-400"
                    />
                    <span className="text-xs mt-2 text-blue-500 font-medium">OCR 도서제목 검출 결과 (확대)</span>
                  </div>
                </div>
                <div className="mb-2 text-lg text-gray-800 dark:text-gray-100 flex items-center justify-center gap-2">
                  <span className="font-bold text-blue-700 dark:text-blue-300">{ocrData.extractedText}</span>
                </div>
                <div className="text-xs text-gray-400 mb-2">{ocrData.createdAt && new Date(ocrData.createdAt).toLocaleString()}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col items-center w-full min-h-full p-4 bg-gradient-to-b from-violet-100 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-900 dark:text-gray-100">
      {/* 업로드 방식 토글 */}
      <UploadModeToggle
        options={[
          { label: "이미지 업로드", value: "image" },
          { label: "URL 업로드", value: "url" }
        ]}
        mode={mode}
        setMode={setMode}
        loading={loading}
      />

      {/* 선택된 UI만 표시 */}
      {mode === "image" ? (
        <div className={`relative w-full max-w-xs border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 flex flex-col items-center mb-6 bg-white dark:bg-gray-800 ${loading ? "pointer-events-none opacity-60" : ""}` }>
          <div className="text-4xl text-gray-400 mb-2">⬆️</div>
          <div className="text-gray-500 dark:text-gray-300 text-center mb-2">
            <span className="font-semibold">이미지 파일을 선택해 주세요</span><br/>
            <span className="text-xs">최대 파일 크기: 10MB</span>
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
            파일 선택
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
          {/* 클립보드 붙여넣기 버튼 */}
          <button
            type="button"
            className="w-full mt-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded hover:bg-gray-300 dark:hover:bg-gray-600 text-xs mb-1"
            onClick={async () => {
              if (navigator.clipboard && navigator.clipboard.readText) {
                try {
                  const text = await navigator.clipboard.readText();
                  setSearch(text);
                } catch (err) {
                  alert("클립보드에서 텍스트를 읽을 수 없습니다. 모바일에서는 직접 붙여넣기 해주세요.");
                }
              } else {
                alert("이 브라우저에서는 클립보드 붙여넣기 기능이 지원되지 않습니다. 직접 붙여넣기 해주세요.");
              }
            }}
            disabled={loading}
          >
            클립보드에서 붙여넣기
          </button>
          {/* URL 업로드 버튼 */}
          <button 
            onClick={handleUrlUpload}
            disabled={loading || !search.trim() || !isValidImageUrl(search)}
            className="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '처리 중...' : 'URL 처리'}
          </button>
          {/* URL 유효성 에러 메시지 */}
          {!loading && search && !isValidImageUrl(search) && (
            <div className="mt-2 text-red-600 dark:text-red-400 text-xs flex items-center gap-1">
              <span>❌</span> 올바른 이미지 URL을 입력해 주세요 (jpg, png, gif 등)
            </div>
          )}
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
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black bg-opacity-70 animate-fadein">
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
              <MdAutoAwesome className="text-3xl align-middle" /> OCR 도서제목 검출 결과
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
                      className="w-32 h-40 object-contain rounded-xl shadow-lg transition-transform duration-200 hover:scale-110"
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
                      className="w-32 h-40 object-contain rounded-xl shadow-lg transition-transform duration-200 hover:scale-110"
                    />
                  )
                ) : (
                  <FallbackImage src="/dummy-image.png" alt="오리지널 이미지" className="w-32 h-40 object-contain rounded-xl shadow-lg transition-transform duration-200 hover:scale-110" />
                )}
                <span className="text-xs mt-2 text-gray-500 font-medium">오리지널 이미지</span>
              </div>
              {/* OCR 박싱 이미지 */}
              <div className="flex flex-col items-center group">
                {ocrResultImage ? (
                  <img 
                    src={ocrResultImage} 
                    alt="OCR 결과 이미지" 
                    className="w-32 h-40 object-contain rounded-xl shadow-lg border-4 border-blue-400 transition-transform duration-200 hover:scale-110 cursor-pointer"
                    onClick={() => {
                      console.log("[LOG] 박싱 이미지 클릭됨, showImageModal=true");
                      setShowImageModal(true);
                    }}
                    onError={(e) => handleImageError(e)}
                  />
                ) : (
                  <FallbackImage src="/dummy-image.png" alt="OCR 결과 이미지" className="w-32 h-40 object-contain rounded-xl shadow-lg border-4 border-blue-400 transition-transform duration-200 hover:scale-110 cursor-pointer" onClick={() => {
                    console.log("[LOG] 박싱 이미지(더미) 클릭됨, showImageModal=true");
                    setShowImageModal(true);
                  }} />
                )}
                <span className="text-xs mt-2 text-blue-500 font-medium">OCR 도서제목 검출 결과</span>
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
              <button className="px-8 py-2 rounded-lg bg-gradient-to-r from-green-400 to-blue-500 text-white font-bold text-base shadow hover:from-green-500 hover:to-blue-600 transition-all duration-200 scale-100 hover:scale-105" onClick={handleOk}>정답</button>
              <button className="px-8 py-2 rounded-lg bg-gradient-to-r from-gray-300 to-gray-400 text-gray-800 font-bold text-base shadow hover:from-gray-400 hover:to-gray-500 transition-all duration-200 scale-100 hover:scale-105" onClick={resetStatus}>오답</button>
            </div>
          </div>
        </div>
      )}
      {/* 확대 모달: status와 무관하게 항상 렌더링 */}
      {showImageModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 animate-fadein">
          <div className="bg-gradient-to-br from-white via-violet-50 to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center relative border-2 border-violet-200 dark:border-gray-700 animate-fadein-up">
            <button
              className="absolute top-4 left-4 text-gray-400 hover:text-violet-600 text-2xl transition-colors"
              onClick={() => setShowImageModal(false)}
              aria-label="닫기"
            >
              ×
            </button>
            <div className="text-2xl font-extrabold mb-4 text-violet-700 dark:text-violet-300 flex items-center justify-center gap-2">
              <span className="text-3xl align-middle">✨</span> OCR 도서제목 검출 결과
            </div>
            <div className="flex justify-center items-end gap-8 mb-6">
              <div className="flex flex-col items-center group">
                <img
                  src={ocrResultImage}
                  alt="OCR 결과 이미지 (확대)"
                  className="max-w-[320px] max-h-[420px] object-contain rounded-xl shadow-lg border-4 border-blue-400"
                />
                <span className="text-xs mt-2 text-blue-500 font-medium">OCR 도서제목 검출 결과 (확대)</span>
              </div>
            </div>
            <div className="mb-2 text-lg text-gray-800 dark:text-gray-100 flex items-center justify-center gap-2">
              <span className="font-bold text-blue-700 dark:text-blue-300">{ocrTitle}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 