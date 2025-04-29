// client/src/components/NewsFlow.jsx
import React, { useState, useEffect } from "react";
import {
  getNewsArticles,
  generateScript,
  generateVideoFromArticle,
} from "../services/api";

const NewsFlow = () => {
  const [loading, setLoading] = useState(false);
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [scriptData, setScriptData] = useState(null);
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState(null);

  // Fetch articles on component mount
  useEffect(() => {
    fetchArticles();
  }, []);

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

    setLoading(true);
    setError(null);

    try {
      const response = await generateScript(selectedArticle.id);

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

  return (
    <div className="news-flow">
      <h2>Generate Video from News</h2>

      {/* Article Selection Section */}
      {!scriptData && (
        <div className="article-selection">
          <h3>Select a News Article</h3>

          {loading && !articles.length ? (
            <p>Loading articles...</p>
          ) : (
            <div className="article-list">
              {articles.map((article) => (
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
              ))}

              {articles.length === 0 && !loading && (
                <p>No articles available. Please try again later.</p>
              )}
            </div>
          )}

          {selectedArticle && (
            <button
              onClick={handleGenerateScript}
              disabled={loading}
              className="primary-button"
            >
              {loading
                ? "Generating Script..."
                : "Generate Script from Selected Article"}
            </button>
          )}
        </div>
      )}

      {/* Script Display Section */}
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
              {loading
                ? "Creating Video (this may take several minutes)..."
                : "Generate Video from Script"}
            </button>
          )}
        </div>
      )}

      {/* Video Display Section */}
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

      {/* Loading Indicator */}
      {loading && !videoData && (
        <div className="loading-indicator">
          <p>Creating video... This process can take several minutes.</p>
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
