import React, { useState, useEffect, useRef } from "react";

const VideoPlayer = ({ videoUrl }) => {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef(null);

  useEffect(() => {
    // Reset states when videoUrl changes
    setError(null);
    setLoading(true);
  }, [videoUrl]);

  const handleVideoError = (e) => {
    console.error("Video error:", e);
    setError(
      `Error loading video: ${e.target.error?.message || "Unknown error"}`
    );
    setLoading(false);
  };

  const handleVideoLoaded = () => {
    console.log("Video loaded successfully:", videoUrl);
    setLoading(false);
  };

  // Try to prefetch video
  useEffect(() => {
    if (videoUrl) {
      const preloadVideo = async () => {
        try {
          const response = await fetch(videoUrl, { method: "HEAD" });
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          console.log(`Video at ${videoUrl} is accessible`);
        } catch (err) {
          console.error(`Video at ${videoUrl} may not be accessible:`, err);
          setError(`Video may not be accessible: ${err.message}`);
        }
      };

      preloadVideo();
    }
  }, [videoUrl]);

  return (
    <div className="video-player">
      {loading && <div className="video-loading">Loading video...</div>}

      {error && (
        <div className="video-error">
          <p>{error}</p>
          <p>URL attempted: {videoUrl}</p>
        </div>
      )}

      <video
        ref={videoRef}
        controls
        width="100%"
        onError={handleVideoError}
        onLoadedData={handleVideoLoaded}
        style={{ background: "#000" }}
      >
        <source src={videoUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
};

export default VideoPlayer;
