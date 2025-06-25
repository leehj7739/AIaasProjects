import React, { useCallback, useState } from "react";

const FALLBACK_SRC = "/dummy-image.png";

const FallbackImage = React.memo(({ src, alt, className, ...props }) => {
  const [imgSrc, setImgSrc] = useState(src && src.trim() !== "" ? src : FALLBACK_SRC);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const handleLoad = useCallback(() => {
    setIsLoading(false);
    setHasError(false);
  }, []);

  const handleError = useCallback(() => {
    if (imgSrc !== FALLBACK_SRC) {
      setImgSrc(FALLBACK_SRC);
      setHasError(true);
      setIsLoading(false);
    }
  }, [imgSrc]);

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
      <img
        src={imgSrc}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
        {...props}
      />
    </div>
  );
});

FallbackImage.displayName = 'FallbackImage';

export default FallbackImage; 