import React, { useState } from 'react';

const MessageBubble = ({
    message,
    align = 'left', // 'left' | 'right'
    backgroundColor = 'bg-white',
    textColor = 'text-gray-800',
    avatarPosition = 'left' // 'left' | 'right'
}) => {
    const isRightAligned = align === 'right';
    const isAvatarLeft = avatarPosition === 'left';
    const [showAllImages, setShowAllImages] = useState(false);

    // 복합 메시지 렌더링 함수
    const renderContent = () => {
        // content가 배열인 경우 (복합 메시지)
        if (Array.isArray(message.content)) {
            return (
                <div className="space-y-2">
                    {message.content.map((item, index) => {
                        if (typeof item === 'string') {
                            // 텍스트인 경우 (줄바꿈 처리)
                            return (
                                <div key={index} className="break-words whitespace-pre-line">
                                    {item}
                                </div>
                            );
                        } else if (item.type === 'image' && item.url) {
                            // 이미지인 경우
                            return (
                                <img
                                    key={index}
                                    src={item.url}
                                    alt={item.alt || `msg-img-${index}`}
                                    className="rounded-md max-w-full max-h-48 object-cover"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                    }}
                                />
                            );
                        } else if (item.type === 'text' && item.content) {
                            // 구조화된 텍스트인 경우
                            return (
                                <div key={index} className="break-words">
                                    {item.content}
                                </div>
                            );
                        }
                        return null;
                    })}
                </div>
            );
        }

        // 기존 구조 호환성 (text + image)
        if (message.content.text || message.content.image) {
            return (
                <div className="space-y-2">
                    {message.content.text && (
                        <div className="break-words whitespace-pre-line">
                            {message.content.text}
                        </div>
                    )}
                    {renderImages()}
                </div>
            );
        }

        return null;
    };

    // 기존 이미지 처리 함수 (호환성 유지)
    const renderImages = () => {
        if (!message.content.image) return null;

        // 배열인 경우 (여러 이미지)
        if (Array.isArray(message.content.image)) {
            const imageCount = message.content.image.length;

            return (
                <div className="space-y-2">
                    <div className="grid grid-cols-2 gap-2 max-w-full">
                        {message.content.image.slice(0, showAllImages ? imageCount : 4).map((imgUrl, index) => (
                            <img
                                key={index}
                                src={imgUrl}
                                alt={`msg-img-${index}`}
                                className="rounded-md w-full h-32 object-cover hover:scale-105 transition-transform duration-200 cursor-pointer"
                                onError={(e) => {
                                    e.target.style.display = 'none';
                                }}
                                onClick={() => {
                                    // 이미지 클릭 시 큰 화면으로 보기
                                    window.open(imgUrl, '_blank');
                                }}
                            />
                        ))}
                    </div>
                    {imageCount > 4 && (
                        <button
                            onClick={() => setShowAllImages(!showAllImages)}
                            className="text-xs text-blue-500 hover:text-blue-700 text-center w-full py-1 rounded hover:bg-blue-50 transition-colors duration-200"
                        >
                            {showAllImages ? '이미지 접기' : `+${imageCount - 4}개의 이미지 더 보기`}
                        </button>
                    )}
                </div>
            );
        }

        // 문자열인 경우 (단일 이미지)
        if (typeof message.content.image === 'string') {
            return (
                <img
                    src={message.content.image}
                    alt="msg-img"
                    className="rounded-md max-w-full max-h-48 object-cover"
                    onError={(e) => {
                        e.target.style.display = 'none';
                    }}
                />
            );
        }

        return null;
    };

    return (
        <div className={`flex ${isRightAligned ? 'justify-end' : 'justify-start'}`}>
            {/* 왼쪽 아바타 */}
            {isAvatarLeft && (
                <img
                    src={message.avatar}
                    alt={message.name}
                    className="w-8 h-8 rounded-full mr-2 self-start"
                />
            )}

            {/* 메시지 내용 */}
            <div>
                <div className={`font-bold text-sm ${isRightAligned ? 'text-right' : ''}`}>
                    {message.name}
                </div>
                <div className={`text-xs text-gray-700 ${isRightAligned ? 'text-right' : ''}`}>
                    {message.time}
                </div>
                <div className={`mt-1 p-2 rounded-lg ${backgroundColor} ${textColor} max-w-[280px]`}>
                    {renderContent()}
                </div>
            </div>

            {/* 오른쪽 아바타 */}
            {!isAvatarLeft && (
                <img
                    src={message.avatar}
                    alt={message.name}
                    className="w-8 h-8 rounded-full ml-2 self-start"
                />
            )}
        </div>
    );
};

export default MessageBubble; 