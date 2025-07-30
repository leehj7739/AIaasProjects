import React, { useState } from 'react';

const MainPage = ({ onNavigateToChat, isConnected = true }) => {
    const [isLoading, setIsLoading] = useState(false);

    const handleStartChat = () => {
        if (!isConnected) {
            alert('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
            return;
        }

        setIsLoading(true);
        // 로딩 효과를 위해 약간의 지연
        setTimeout(() => {
            setIsLoading(false);
            onNavigateToChat();
        }, 1500);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
            <div className="max-w-4xl mx-auto text-center">
                {/* 헤더 */}
                <div className="mb-12">
                    <div className="flex justify-center mb-6">
                        <div className="w-20 h-20 bg-gradient-to-r from-teal-400 to-blue-500 rounded-full flex items-center justify-center shadow-lg">
                            <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h10a4 4 0 004-4V7a4 4 0 00-4-4H7a4 4 0 00-4 4v8z" />
                            </svg>
                        </div>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-bold text-gray-800 mb-4">
                        영화챗봇
                    </h1>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        AI와 함께하는 영화 탐험의 세계로 떠나보세요
                    </p>

                    {/* 연결 상태 표시 */}
                    <div className="mt-4 flex justify-center">
                        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${isConnected
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                            <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'
                                }`}></div>
                            {isConnected ? '서버 연결됨' : '서버 연결 끊김'}
                        </div>
                    </div>
                </div>

                {/* 연결 경고 메시지 */}
                {!isConnected && (
                    <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl mx-auto">
                        <div className="flex items-center">
                            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                            <span className="text-red-700 font-medium">서버에 연결할 수 없습니다</span>
                        </div>
                        <p className="text-red-600 text-sm mt-1">
                            백엔드 서버가 실행 중인지 확인해주세요. (http://127.0.0.1:8000)
                        </p>
                    </div>
                )}

                {/* 메인 콘텐츠 */}
                <div className="grid md:grid-cols-3 gap-8 mb-12">
                    {/* 기능 1 */}
                    <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                            <svg className="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">영화 검색</h3>
                        <p className="text-gray-600">
                            원하는 영화를 자연스러운 대화로 찾아보세요
                        </p>
                    </div>

                    {/* 기능 2 */}
                    <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300">
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                            <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">실시간 추천</h3>
                        <p className="text-gray-600">
                            AI가 당신의 취향을 분석해서 맞춤 영화를 추천해드려요
                        </p>
                    </div>

                    {/* 기능 3 */}
                    <div className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-300">
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                            <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">자연스러운 대화</h3>
                        <p className="text-gray-600">
                            복잡한 검색 없이 대화하듯 영화 정보를 얻어보세요
                        </p>
                    </div>
                </div>

                {/* 시작 버튼 */}
                <div className="mb-8">
                    <button
                        onClick={handleStartChat}
                        disabled={isLoading || !isConnected}
                        className={`px-8 py-4 rounded-full text-lg font-semibold transition-all duration-300 transform hover:scale-105 ${isLoading || !isConnected
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-teal-400 to-blue-500 hover:from-teal-500 hover:to-blue-600'
                            } text-white shadow-lg hover:shadow-xl`}
                    >
                        {isLoading ? (
                            <div className="flex items-center">
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                챗봇 준비 중...
                            </div>
                        ) : !isConnected ? (
                            '서버 연결 필요'
                        ) : (
                            '챗봇 시작하기'
                        )}
                    </button>
                </div>

                {/* 하단 정보 */}
                <div className="text-gray-500 text-sm">
                    <p>24시간 언제든지 이용 가능한 AI 영화 어시스턴트</p>
                </div>
            </div>
        </div>
    );
};

export default MainPage; 