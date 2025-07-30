import React, { useEffect, useState } from 'react';

const LoadingPage = ({ onLoadingComplete, isLoading = false }) => {
    const [loadingText, setLoadingText] = useState('');
    const [currentStep, setCurrentStep] = useState(0);

    const loadingSteps = [
        'AI 모델을 초기화하고 있습니다...',
        '영화 데이터베이스를 연결하고 있습니다...',
        '챗봇 시스템을 준비하고 있습니다...',
        '대화 환경을 설정하고 있습니다...',
        '거의 완료되었습니다...'
    ];

    useEffect(() => {
        // isLoading이 false이면 즉시 완료
        if (!isLoading) {
            onLoadingComplete();
            return;
        }

        const interval = setInterval(() => {
            if (currentStep < loadingSteps.length) {
                setLoadingText(loadingSteps[currentStep]);
                setCurrentStep(prev => prev + 1);
            } else {
                clearInterval(interval);
                // 로딩 완료 후 약간의 지연을 두고 완료 콜백 호출
                setTimeout(() => {
                    onLoadingComplete();
                }, 500);
            }
        }, 800);

        return () => clearInterval(interval);
    }, [currentStep, loadingSteps.length, onLoadingComplete, isLoading]);

    // isLoading이 false이면 로딩 화면을 건너뛰고 즉시 완료
    if (!isLoading) {
        return null;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
            <div className="text-center">
                {/* 로딩 애니메이션 */}
                <div className="mb-8">
                    <div className="relative">
                        {/* 메인 로딩 원 */}
                        <div className="w-32 h-32 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin mx-auto"></div>

                        {/* 내부 아이콘 */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-16 h-16 bg-gradient-to-r from-teal-400 to-blue-500 rounded-full flex items-center justify-center shadow-lg">
                                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h10a4 4 0 004-4V7a4 4 0 00-4-4H7a4 4 0 00-4 4v8z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 로딩 텍스트 */}
                <div className="mb-6">
                    <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                        영화챗봇 준비 중
                    </h2>
                    <p className="text-blue-200 text-lg min-h-[2rem] flex items-center justify-center">
                        {loadingText}
                    </p>
                </div>

                {/* 진행률 표시 */}
                <div className="mb-8">
                    <div className="w-64 bg-blue-800 rounded-full h-2 mx-auto">
                        <div
                            className="bg-gradient-to-r from-teal-400 to-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
                            style={{ width: `${((currentStep) / loadingSteps.length) * 100}%` }}
                        ></div>
                    </div>
                    <p className="text-blue-300 text-sm mt-2">
                        {Math.round(((currentStep) / loadingSteps.length) * 100)}%
                    </p>
                </div>

                {/* 부가 정보 */}
                <div className="text-blue-300 text-sm">
                    <p>잠시만 기다려주세요...</p>
                </div>

                {/* 배경 애니메이션 요소들 */}
                <div className="fixed inset-0 pointer-events-none overflow-hidden">
                    {[...Array(6)].map((_, i) => (
                        <div
                            key={i}
                            className="absolute w-2 h-2 bg-blue-400 rounded-full animate-pulse"
                            style={{
                                left: `${Math.random() * 100}%`,
                                top: `${Math.random() * 100}%`,
                                animationDelay: `${i * 0.5}s`,
                                animationDuration: `${2 + Math.random() * 2}s`
                            }}
                        ></div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default LoadingPage; 