import React, { useState, useEffect } from "react";
import VideoPlayer from "./VideoPlayer";
import { generateScript, generateVideoFromArticle } from "../services/api";

const ScriptGenerator = ({ articleId, articleTitle }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scriptData, setScriptData] = useState(null);
  const [videoData, setVideoData] = useState(null);
  const [generatingVideo, setGeneratingVideo] = useState(false);

  // For debugging - log important state changes
  useEffect(() => {
    console.log("ScriptGenerator state:", {
      hasVideo: !!videoData,
      videoUrl: videoData?.video_url,
      scriptId: scriptData?.script_id,
      error,
    });
  }, [videoData, scriptData, error]);

  // Generate script when component mounts with an articleId
  useEffect(() => {
    if (articleId) {
      generateScriptFromArticle(articleId);
    }
  }, [articleId]);

  const generateScriptFromArticle = async (id) => {
    setLoading(true);
    setError(null);
    setVideoData(null); // Reset video data when generating new script

    try {
      const response = await generateScript(id);
      if (response.success) {
        setScriptData(response.data);
        console.log("Script generated successfully:", response.data);
      } else {
        setError(response.error || "Failed to generate script");
        console.error("Script generation failed:", response.error);
      }
    } catch (err) {
      const errorMessage = err.message || "Error connecting to server";
      setError(errorMessage);
      console.error("Script generation error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVideo = async () => {
    if (!scriptData) return;

    setGeneratingVideo(true);
    setError(null);

    try {
      console.log("Generating video for script ID:", scriptData.script_id);
      const response = await generateVideoFromArticle(scriptData.script_id);

      console.log("Video generation response:", response);

      if (response.success) {
        setVideoData(response.data);
      } else {
        setError(response.error || "Failed to generate video");
        console.error("Video generation failed:", response.error);
      }
    } catch (err) {
      const errorMessage = err.message || "Error connecting to server";
      setError(errorMessage);
      console.error("Video generation error:", err);
    } finally {
      setGeneratingVideo(false);
    }
  };

  // Proper rendering with return statement and debugging info
  return (
    <div className="script-generator">
      <h2>Script Generator {articleTitle ? `for "${articleTitle}"` : ""}</h2>

      {loading && <div className="loading-indicator">Generating script...</div>}

      {error && (
        <div className="error-message">
          <h3>Error:</h3>
          <p>{error}</p>
        </div>
      )}

      {scriptData && !videoData && !loading && (
        <div className="generated-script">
          <h3>Generated Script for: {scriptData.title}</h3>
          <div className="script-content">
            {scriptData.script.split("\n").map((para, idx) => (
              <p key={idx}>{para}</p>
            ))}
          </div>

          <button
            className="primary-button"
            onClick={handleCreateVideo}
            disabled={generatingVideo}
          >
            {generatingVideo
              ? "Generating Video..."
              : "Create Video from Script"}
          </button>
        </div>
      )}

      {videoData && (
        <div className="video-container">
          <h3>Generated Video</h3>
          <VideoPlayer videoUrl={videoData.video_url} />

          {/* Debug info */}
          <div
            className="debug-info"
            style={{ fontSize: "12px", color: "#666", marginTop: "10px" }}
          >
            <p>Video URL: {videoData.video_url}</p>
            <p>Video ID: {videoData.video_id}</p>
          </div>
        </div>
      )}

      {/* Debug section to show what's happening */}
      <div
        className="debug-section"
        style={{
          margin: "30px 0",
          padding: "15px",
          background: "#f8f8f8",
          borderRadius: "5px",
          fontSize: "12px",
        }}
      >
        <h4>Debug Info:</h4>
        <pre>
          {JSON.stringify(
            {
              hasArticleId: !!articleId,
              hasScriptData: !!scriptData,
              hasVideoData: !!videoData,
              videoUrl: videoData?.video_url,
              isLoading: loading,
              isGeneratingVideo: generatingVideo,
              error,
            },
            null,
            2
          )}
        </pre>
      </div>
    </div>
  );
};

export default ScriptGenerator;
