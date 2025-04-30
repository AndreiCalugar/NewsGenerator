// client/src/components/NewsFlow.jsx
import React, { useState, useEffect, useRef } from "react";
import {
  fetchNewsArticles as getNewsArticles,
  generateScript,
  generateVideoFromArticle,
} from "../services/api";
import VideoPlayer from "./VideoPlayer";

const NewsFlow = ({ videoData, setVideoData }) => {
  const [loading, setLoading] = useState(false);
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [scriptData, setScriptData] = useState(null);
  const [error, setError] = useState(null);
  const [scriptLoading, setScriptLoading] = useState(false);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const timerRef = useRef(null);

  // Fetch articles on component mount
  useEffect(() => {
    fetchArticles();
  }, []);

  // Start timer when video generation begins
  useEffect(() => {
    if (loading && !videoData) {
      // Reset timer
      setTimeElapsed(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setTimeElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      // Clear timer when loading ends
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    // Cleanup when component unmounts
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [loading, videoData]);

  const fetchArticles = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getNewsArticles();

      if (response.success) {
        setArticles(response.data.articles);
      } else {
        setError(response.error || "Failed to fetch news articles");
      }
    } catch (err) {
      setError(err.error || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleArticleSelect = (article) => {
    setSelectedArticle(article);
    // Clear any previous script or video data when selecting a new article
    setScriptData(null);
    setVideoData(null);
  };

  const handleGenerateScript = async () => {
    if (!selectedArticle) return;

    try {
      setScriptLoading(true);
      setError(null);

      console.log("Generating script for article:", selectedArticle.id);
      const response = await generateScript(selectedArticle.id);

      if (response.success) {
        setScriptData(response.data);
        console.log("Script generated:", response.data);
      } else {
        setError(response.error || "Failed to generate script");
        console.error("Script generation failed:", response.error);
      }
    } catch (error) {
      // This should not happen anymore
      console.error("Unexpected error in script generation:", error);
      setError("An unexpected error occurred");
    } finally {
      setScriptLoading(false);
    }
  };

  const handleCreateVideo = async () => {
    if (!scriptData?.script_id) return;

    setLoading(true);
    setError(null);

    try {
      // Add clear message for user
      console.log(
        "Starting video generation - this may take several minutes..."
      );

      const response = await generateVideoFromArticle(scriptData.script_id);

      if (response.success) {
        setVideoData(response.data);
      } else {
        setError(response.error || "Failed to create video");
      }
    } catch (err) {
      console.error("Video generation error:", err);
      setError(
        err.error ||
          "Failed to connect to server. Video generation may take several minutes - please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const debugVideoURL = (url) => {
    // The server returns paths like "/videos/filename.mp4"
    // We need to build a direct URL to the server
    const fullUrl = `http://localhost:5000${url}`;

    return (
      <div className="debug-url">
        <p>
          <strong>URL from API:</strong> {url}
        </p>
        <p>
          <strong>Full URL:</strong> {fullUrl}
        </p>
        <button
          className="debug-button"
          onClick={() => window.open(fullUrl, "_blank")}
        >
          Test in New Tab
        </button>
      </div>
    );
  };

  // Add this helper function
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" + secs : secs}`;
  };

  // Add a reset function to clear video and script data
  const handleReset = () => {
    setVideoData(null);
    setScriptData(null);
    setSelectedArticle(null);
    setError(null);
  };

  return (
    <div className="news-flow">
      <h2 className="section-headline">
        Turn Today's Headlines into Short Videos
      </h2>

      {/* Article Selection Section - Show only if no script or video yet */}
      {!scriptData && !videoData && (
        <div className="article-selection">
          <div className="article-header">
            <h3>1. Select a News Article</h3>
            <button
              onClick={fetchArticles}
              disabled={loading}
              className="refresh-button"
              title="Get the latest news articles"
            >
              ↻ Refresh Articles
            </button>
          </div>

          {loading && !articles.length ? (
            <p>Loading articles...</p>
          ) : (
            <div className="article-list">
              {articles.length === 0 && !loading ? (
                <p>No articles available. Please try again later.</p>
              ) : (
                articles.map((article) => (
                  <div
                    key={article.id}
                    className={`article-card ${
                      selectedArticle?.id === article.id ? "selected" : ""
                    }`}
                    onClick={() => handleArticleSelect(article)}
                  >
                    <h4>{article.title}</h4>
                    <div className="article-source">{article.source}</div>
                    <p>{article.description}</p>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Generate Script button */}
          {selectedArticle && (
            <button
              onClick={handleGenerateScript}
              disabled={scriptLoading}
              className="primary-button"
              title="Create a script from this article"
            >
              {scriptLoading ? "Generating Script..." : "Generate Script"}
            </button>
          )}
        </div>
      )}

      {/* Script Display Section - Show when script is generated but no video yet */}
      {scriptData && !videoData && (
        <div className="script-card">
          <h3>{scriptData.title}</h3>
          <div className="script-content">
            <p>{scriptData.script}</p>
          </div>

          {/* Generate Video button */}
          <button
            onClick={handleCreateVideo}
            disabled={loading}
            className="primary-button"
            title="Create a video from this script"
          >
            {loading
              ? "Creating Video (this may take several minutes)..."
              : "Generate Video from Script"}
          </button>
        </div>
      )}

      {/* Video Display Section - Show when video is ready */}
      {videoData && (
        <div className="video-result">
          <h3 className="section-headline">
            Generated Video: {videoData.title}
          </h3>
          <div className="video-player">
            {debugVideoURL(videoData.video_url)}
            <video
              controls
              width="100%"
              src={`http://localhost:5000${videoData.video_url}`}
              onError={(e) => console.error("Video error:", e)}
            >
              Your browser does not support the video tag.
            </video>
          </div>
          <div
            className="debug-info"
            style={{ fontSize: "12px", color: "#666", marginTop: "10px" }}
          >
            <p>Video ID: {videoData.video_id}</p>
          </div>

          {/* Generate Another Video button */}
          <button
            className="secondary-button"
            onClick={handleReset}
            title="Start over with a new video"
          >
            Generate Another Video
          </button>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && !videoData && (
        <div className="loading-indicator">
          <p>Creating video... Time elapsed: {formatTime(timeElapsed)}</p>
          <p>
            This process can take several minutes. The longer the text, the more
            time it takes.
          </p>
          <p>Please don't close the browser window.</p>
          <div className="progress-animation"></div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default NewsFlow;
