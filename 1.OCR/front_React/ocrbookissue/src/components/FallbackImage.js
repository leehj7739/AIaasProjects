import React from "react";

const FALLBACK_SRC = "/dummy-image.png";

export default function FallbackImage({ src, alt, ...props }) {
  const handleError = e => {
    if (!e.target.src.endsWith(FALLBACK_SRC)) {
      e.target.src = FALLBACK_SRC;
    }
  };
  return (
    <img
      src={src && src.trim() !== "" ? src : FALLBACK_SRC}
      alt={alt}
      onError={handleError}
      {...props}
    />
  );
} 