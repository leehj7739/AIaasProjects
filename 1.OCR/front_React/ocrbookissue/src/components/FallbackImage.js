import React, { useCallback } from "react";

const FALLBACK_SRC = "/dummy-image.png";

const FallbackImage = React.memo(({ src, alt, ...props }) => {
  const handleError = useCallback(e => {
    if (!e.target.src.endsWith(FALLBACK_SRC)) {
      e.target.src = FALLBACK_SRC;
    }
  }, []);

  return (
    <img
      src={src && src.trim() !== "" ? src : FALLBACK_SRC}
      alt={alt}
      onError={handleError}
      {...props}
    />
  );
});

FallbackImage.displayName = 'FallbackImage';

export default FallbackImage; 