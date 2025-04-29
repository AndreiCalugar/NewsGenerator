// client/src/components/NewsFlow.jsx
import React, { useState } from "react";
import { generateScript, generateVideoFromArticle } from "../services/api";

const NewsFlow = () => {
  const [loading, setLoading] = useState(false);
  const [scriptData, setScriptData] = useState(null);
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerateScript = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await generateScript();

      if (response.success) {
        setScriptData(response.data);
      } else {
        setError(response.error || "Failed to generate script");
      }
    } catch (err) {
      setError(err.error || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVideo = async () => {
    if (!scriptData?.script_id) return;

    setLoading(true);
    setError(null);

    try {
      const response = await generateVideoFromArticle(scriptData.script_id);

      if (response.success) {
        setVideoData(response.data);
      } else {
        setError(response.error || "Failed to create video");
      }
    } catch (err) {
      setError(err.error || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="news-flow">
      <h2>Generate Video from News</h2>

      {!scriptData && (
        <button
          onClick={handleGenerateScript}
          disabled={loading}
          className="primary-button"
        >
          {loading ? "Generating Script..." : "Generate Script from News"}
        </button>
      )}

      {scriptData && (
        <div className="script-card">
          <h3>{scriptData.title}</h3>
          <div className="script-content">
            <p>{scriptData.script}</p>
          </div>

          {!videoData && (
            <button
              onClick={handleCreateVideo}
              disabled={loading}
              className="primary-button"
            >
              {loading ? "Creating Video..." : "Generate Video from Script"}
            </button>
          )}
        </div>
      )}

      {videoData && (
        <div className="video-result">
          <h3>Video Created: {videoData.title}</h3>
          <div className="video-player">
            <video
              controls
              width="100%"
              src={
                videoData.video_path.startsWith("http")
                  ? videoData.video_path // Use direct URL for mock data
                  : `http://localhost:5000${videoData.video_path}` // Use server path for real data
              }
            />
          </div>
          <a
            href={
              videoData.video_path.startsWith("http")
                ? videoData.video_path
                : `http://localhost:5000${videoData.video_path}`
            }
            target="_blank"
            rel="noopener noreferrer"
            className="download-link"
          >
            Download Video
          </a>
        </div>
      )}

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default NewsFlow;
