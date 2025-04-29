// client/src/components/CustomTextFlow.jsx
import React, { useState } from "react";
import { generateVideoFromCustomText } from "../services/api";

const CustomTextFlow = () => {
  const [formData, setFormData] = useState({
    title: "",
    text: "",
  });
  const [loading, setLoading] = useState(false);
  const [videoData, setVideoData] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.title || !formData.text) {
      setError("Please provide both title and text");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await generateVideoFromCustomText(
        formData.title,
        formData.text
      );

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

  const handleReset = () => {
    setFormData({ title: "", text: "" });
    setVideoData(null);
    setError(null);
  };

  return (
    <div className="custom-text-flow">
      <h2>Generate Video from Custom Text</h2>

      {!videoData ? (
        <form onSubmit={handleSubmit} className="custom-text-form">
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Enter a title for your video"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="text">Text Content</label>
            <textarea
              id="text"
              name="text"
              value={formData.text}
              onChange={handleChange}
              placeholder="Enter the text content for your video"
              rows={8}
              required
            />
          </div>

          <button type="submit" disabled={loading} className="primary-button">
            {loading ? "Creating Video..." : "Create Video from Text"}
          </button>
        </form>
      ) : (
        <div className="video-result">
          <h3>Video Created: {videoData.title}</h3>

          <div className="video-container">
            <div className="video-player">
              <h4>Standard Video</h4>
              <video
                controls
                width="100%"
                src={
                  videoData.video_url.startsWith("http")
                    ? videoData.video_url // Use direct URL for mock data
                    : `http://localhost:5000${videoData.video_url}` // Use server path for real data
                }
              />
              <a
                href={`http://localhost:5000${videoData.video_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="download-link"
              >
                Download Standard Video
              </a>
            </div>

            {videoData.vertical_video_url && (
              <div className="video-player">
                <h4>Vertical Video (Social Media)</h4>
                <video
                  controls
                  width="100%"
                  src={
                    videoData.vertical_video_url.startsWith("http")
                      ? videoData.vertical_video_url // Use direct URL for mock data
                      : `http://localhost:5000${videoData.vertical_video_url}` // Use server path for real data
                  }
                />
                <a
                  href={`http://localhost:5000${videoData.vertical_video_url}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="download-link"
                >
                  Download Vertical Video
                </a>
              </div>
            )}
          </div>

          <div className="keywords">
            <h4>Keywords:</h4>
            <div className="keyword-list">
              {videoData.keywords &&
                videoData.keywords.map((keyword, idx) => (
                  <span key={idx} className="keyword-tag">
                    {keyword}
                  </span>
                ))}
            </div>
          </div>

          <button onClick={handleReset} className="secondary-button">
            Create Another Video
          </button>
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

export default CustomTextFlow;
