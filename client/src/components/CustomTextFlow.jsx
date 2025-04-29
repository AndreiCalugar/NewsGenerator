// client/src/components/CustomTextFlow.jsx
import React, { useState, useEffect, useRef } from "react";
import { generateVideoFromCustomText } from "../services/api";
import VideoPlayer from "./VideoPlayer";

const CustomTextFlow = () => {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState(null);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const timerRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim() || !text.trim()) {
      setError("Please enter both a title and text content");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log("Generating video from custom text:", {
        title,
        textLength: text.length,
      });

      const response = await generateVideoFromCustomText(title, text);
      console.log("Video generation response:", response);

      if (response.success) {
        setVideoData(response.data);
      } else {
        setError(response.error || "Failed to generate video");
      }
    } catch (err) {
      // This shouldn't happen anymore since our API functions return objects instead of throwing
      console.error("Unexpected error generating video:", err);
      setError("An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setTitle("");
    setText("");
    setVideoData(null);
    setError(null);
  };

  useEffect(() => {
    if (videoData) {
      console.log("Video URLs:", {
        standard: `http://localhost:5000${videoData.video_url}`,
        vertical: videoData.vertical_video_url
          ? `http://localhost:5000${videoData.vertical_video_url}`
          : null,
      });

      // Test if video is accessible
      fetch(`http://localhost:5000${videoData.video_url}`, { method: "HEAD" })
        .then((response) => {
          console.log("Video accessibility check:", {
            status: response.status,
            ok: response.ok,
            url: `http://localhost:5000${videoData.video_url}`,
          });
        })
        .catch((err) => {
          console.error("Video fetch error:", err);
        });
    }
  }, [videoData]);

  useEffect(() => {
    if (loading) {
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
  }, [loading]);

  const debugVideoURL = (url) => {
    // Extract just the filename for brevity
    const filename = url.split("/").pop();

    // Build the full URL
    const fullUrl = `http://localhost:5000${url}`;

    return (
      <div className="debug-url">
        <p>
          <strong>URL:</strong> {url}
        </p>
        <p>
          <strong>Full URL:</strong> {fullUrl}
        </p>
        <button onClick={() => window.open(fullUrl, "_blank")}>
          Test Direct URL
        </button>
        <button
          onClick={() =>
            fetch(fullUrl, { method: "HEAD" })
              .then((response) =>
                alert(
                  `Status: ${response.status} ${response.ok ? "OK" : "Failed"}`
                )
              )
              .catch((err) => alert(`Fetch error: ${err.message}`))
          }
        >
          Check URL
        </button>
      </div>
    );
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" + secs : secs}`;
  };

  return (
    <div className="custom-text-flow">
      <h2>Custom Text to Video Generator</h2>

      {error && <div className="error-message">{error}</div>}

      {!videoData ? (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title:</label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for your video"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="text">Text Content:</label>
            <textarea
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter the text content for your video"
              rows={8}
              disabled={loading}
            />
            <div className="character-count">
              {text.length} characters /{" "}
              {text.split(/\s+/).filter(Boolean).length} words
            </div>
          </div>

          <button
            type="submit"
            className="primary-button"
            disabled={loading || !title.trim() || !text.trim()}
          >
            {loading ? "Generating Video..." : "Generate Video"}
          </button>
        </form>
      ) : (
        <div className="result-container">
          <h3>Generated Video: {videoData.title}</h3>

          <div className="video-result">
            <h3>Video Created: {videoData.title}</h3>

            <div className="video-container">
              <h4>Standard Video</h4>
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

            {videoData.vertical_video_url && (
              <div className="video-container vertical">
                <h4>Vertical Video (Social Media)</h4>
                <video
                  controls
                  width="100%"
                  src={`http://localhost:5000${videoData.vertical_video_url}`}
                  onError={(e) => console.error("Video error:", e)}
                >
                  Your browser does not support the video tag.
                </video>
              </div>
            )}
          </div>

          <div className="keywords">
            <h4>Keywords:</h4>
            <div className="keyword-list">
              {videoData.keywords &&
                videoData.keywords.map((keyword, index) => (
                  <span key={index} className="keyword-tag">
                    {keyword}
                  </span>
                ))}
            </div>
          </div>

          <button className="secondary-button" onClick={handleReset}>
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

      {loading && (
        <div className="loading-indicator">
          <p>Generating video... Time elapsed: {formatTime(timeElapsed)}</p>
          <p>This process can take several minutes for longer texts.</p>
          <p>Please don't close this page while the video is being created.</p>
          <div className="progress-animation"></div>
        </div>
      )}
    </div>
  );
};

export default CustomTextFlow;
