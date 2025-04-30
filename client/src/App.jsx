// client/src/App.jsx
import React, { useState } from "react";
import NewsFlow from "./components/NewsFlow";
import CustomTextFlow from "./components/CustomTextFlow";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("news");

  // Add shared state for videos that persists between tab changes
  const [newsVideoData, setNewsVideoData] = useState(null);
  const [customVideoData, setCustomVideoData] = useState(null);

  return (
    <div className="app-container">
      <header className="header">
        <h1>AutoVid</h1>
        <p>Generate videos from news articles or custom text</p>
      </header>

      <main className="main-content">
        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === "news" ? "active" : ""}`}
            onClick={() => setActiveTab("news")}
            title="Convert news articles into video content"
          >
            <span className="tab-icon">📰</span> News to Video
          </button>
          <button
            className={`tab-button ${activeTab === "custom" ? "active" : ""}`}
            onClick={() => setActiveTab("custom")}
            title="Create videos from your own text"
          >
            <span className="tab-icon">✏️</span> Custom Text to Video
          </button>
        </div>

        {activeTab === "news" ? (
          <NewsFlow videoData={newsVideoData} setVideoData={setNewsVideoData} />
        ) : (
          <CustomTextFlow
            videoData={customVideoData}
            setVideoData={setCustomVideoData}
          />
        )}
      </main>

      <footer className="footer">
        <p>© 2025 AutoVid - AI-Powered Video Generation</p>
      </footer>
    </div>
  );
}

export default App;
