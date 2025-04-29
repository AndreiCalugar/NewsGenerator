// client/src/App.jsx
import React, { useState } from "react";
import NewsFlow from "./components/NewsFlow";
import CustomTextFlow from "./components/CustomTextFlow";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("news");

  return (
    <div className="app-container">
      <header className="header">
        <h1>AutoVid - Video Generator</h1>
      </header>

      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === "news" ? "active" : ""}`}
          onClick={() => setActiveTab("news")}
        >
          News to Video
        </button>
        <button
          className={`tab-button ${activeTab === "custom" ? "active" : ""}`}
          onClick={() => setActiveTab("custom")}
        >
          Custom Text to Video
        </button>
      </div>

      <main className="main-content">
        {activeTab === "news" ? <NewsFlow /> : <CustomTextFlow />}
      </main>

      <footer className="footer">
        <p>AutoVid - Video Generation Tool</p>
      </footer>
    </div>
  );
}

export default App;
