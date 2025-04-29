import React, { useState } from "react";
import VideoPlayer from "./VideoPlayer";
import { generateVideoFromCustomText } from "../services/api";

const CustomTextForm = () => {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [generating, setGenerating] = useState(false);
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim() || !text.trim()) {
      setError("Both title and text are required");
      return;
    }

    setError(null);
    setGenerating(true);

    try {
      console.log("Generating video from custom text:", {
        title,
        textLength: text.length,
      });
      const response = await generateVideoFromCustomText(title, text);

      console.log("Response from video generation:", response);

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
      setGenerating(false);
    }
  };

  return (
    <div className="custom-text-form">
      <h1>Generate Video from Custom Text</h1>

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {!videoData && (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title:</label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for your video"
              disabled={generating}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="text">Text Content:</label>
            <textarea
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter the text content for your video script"
              rows={10}
              disabled={generating}
              required
            />
            <div className="text-count">
              {text.split(/\s+/).filter(Boolean).length} words
            </div>
          </div>

          <button
            type="submit"
            className="primary-button"
            disabled={generating || !title.trim() || !text.trim()}
          >
            {generating ? "Generating Video..." : "Generate Video"}
          </button>
        </form>
      )}

      {videoData && (
        <div className="video-result">
          <h2>Generated Video: {videoData.title}</h2>

          <div className="video-container">
            <h3>Regular Video</h3>
            <VideoPlayer videoUrl={videoData.video_url} />
          </div>

          {videoData.vertical_video_url && (
            <div className="video-container vertical">
              <h3>Vertical Video (for Social Media)</h3>
              <VideoPlayer videoUrl={videoData.vertical_video_url} />
            </div>
          )}

          <button
            className="secondary-button"
            onClick={() => {
              setVideoData(null);
              setTitle("");
              setText("");
            }}
          >
            Create Another Video
          </button>

          <div
            className="debug-info"
            style={{ fontSize: "12px", color: "#666", marginTop: "10px" }}
          >
            <p>Video URL: {videoData.video_url}</p>
            {videoData.vertical_video_url && (
              <p>Vertical Video URL: {videoData.vertical_video_url}</p>
            )}
            <p>Video ID: {videoData.video_id}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomTextForm;
