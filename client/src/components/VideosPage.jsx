import React, { useState, useEffect } from "react";
import { fetchVideos } from "../services/api";
import VideoPlayer from "./VideoPlayer";

const VideosPage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadVideos = async () => {
      try {
        setLoading(true);
        const response = await fetchVideos();
        if (response.success) {
          setVideos(response.data.videos);
        } else {
          setError(response.error || "Failed to load videos");
        }
      } catch (err) {
        setError("Error connecting to server");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadVideos();
  }, []);

  return (
    <div className="videos-page">
      <h2>Generated Videos</h2>

      {loading && <p>Loading videos...</p>}

      {error && <div className="error-message">{error}</div>}

      {!loading && videos.length === 0 && !error && (
        <p>No videos have been generated yet.</p>
      )}

      <div className="videos-grid">
        {videos.map((video) => (
          <div key={video.id} className="video-card">
            <h3>{video.title}</h3>
            <VideoPlayer videoUrl={video.video_url} />
            <p>Created: {new Date(video.created_at).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VideosPage;
