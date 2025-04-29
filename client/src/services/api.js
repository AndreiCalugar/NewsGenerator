// client/src/services/api.js
import axios from "axios";

const API_URL = "http://localhost:5000/api";

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 60 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

// Special instance with even longer timeout for video generation
const videoGenAxios = axios.create({
  baseURL: API_URL,
  timeout: 600000, // 10 minutes
  headers: {
    "Content-Type": "application/json",
  },
});

// Add this utility function to your API service
const checkServerStatus = async () => {
  try {
    // Check if server is running with a simple HEAD request
    const response = await fetch(`${API_URL}/health`, { method: "HEAD" });
    return response.ok;
  } catch (error) {
    console.error("Server connectivity check failed:", error);
    return false;
  }
};

// Update the response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    console.log(`API Response [${response.config.url}]:`, response.data);
    return response;
  },
  async (error) => {
    console.error("API Error:", error);

    // First check if server is reachable at all
    const serverAlive = await checkServerStatus().catch(() => false);

    if (!serverAlive) {
      return Promise.resolve({
        data: {
          success: false,
          error:
            "Server is not responding. Please ensure the server is running.",
          data: null,
        },
      });
    }

    // If there's a response, return it
    if (error.response) {
      return Promise.resolve({
        data: {
          success: false,
          error:
            error.response.data?.error ||
            `Server error: ${error.response.status}`,
          data: null,
        },
      });
    }

    // For network errors
    return Promise.resolve({
      data: {
        success: false,
        error: error.message || "Network error occurred",
        data: null,
      },
    });
  }
);

// Enable for testing without backend
const USE_MOCK_API = false;

export const fetchNewsArticles = async () => {
  if (USE_MOCK_API) {
    // Return mock data for testing
    await new Promise((resolve) => setTimeout(resolve, 500)); // Simulate loading
    return {
      success: true,
      data: {
        articles: [
          {
            id: 1,
            title: "Scientists Develop New Renewable Energy Technology",
            source: "Science Daily",
            description:
              "Researchers have developed a breakthrough technology that can convert ambient heat into electricity with unprecedented efficiency.",
          },
          {
            id: 2,
            title: "Global Economic Summit Addresses Climate Challenges",
            source: "Financial Times",
            description:
              "World leaders met in Geneva this week to address the economic implications of climate change.",
          },
          {
            id: 3,
            title:
              "New AI System Can Diagnose Medical Conditions with 99% Accuracy",
            source: "Health Tech Today",
            description:
              "A groundbreaking artificial intelligence system has demonstrated the ability to diagnose a wide range of medical conditions.",
          },
        ],
      },
      error: null,
    };
  }

  try {
    const response = await axiosInstance.get("/news_articles");
    return response.data;
  } catch (error) {
    console.error("Error fetching news articles:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Could not connect to server",
      data: null,
    };
  }
};

export const getArticleById = async (id) => {
  if (USE_MOCK_API) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return {
      success: true,
      data: {
        id: id,
        title: "Sample Article " + id,
        source: "Mock News",
        description:
          "This is a sample article description for testing purposes.",
        content:
          "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam euismod, nisl eget ultricies aliquam, nunc nisl ultricies nunc, vitae ultricies nisl nisl eget nunc.",
        published_at: new Date().toISOString(),
      },
      error: null,
    };
  }

  try {
    const response = await axiosInstance.get(`/articles/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching article:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch article",
    };
  }
};

export const generateScript = async (articleId) => {
  if (USE_MOCK_API) {
    await new Promise((resolve) => setTimeout(resolve, 1500)); // Simulate processing time
    return {
      success: true,
      data: {
        script_id: 100,
        article_id: articleId,
        title: "Sample Article Title",
        script:
          "This is a sample script generated for the article. It would typically be longer and more detailed, covering the main points of the news article in a format suitable for video narration.\n\nThe script would continue with more paragraphs explaining the news story in detail.",
      },
      error: null,
    };
  }

  try {
    const response = await axiosInstance.post("/generate_script", {
      article_id: articleId,
    });
    return response.data;
  } catch (error) {
    console.error("Error generating script:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Could not connect to server",
      data: null,
    };
  }
};

export const generateVideoFromArticle = async (scriptId) => {
  if (USE_MOCK_API) {
    // Mock response for testing without backend
    await new Promise((resolve) => setTimeout(resolve, 3000)); // Simulate processing
    return {
      success: true,
      data: {
        video_id: 123,
        script_id: scriptId,
        video_url:
          "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4", // Sample video URL
        title: "Sample Video Title",
      },
      error: null,
    };
  }

  try {
    const response = await videoGenAxios.post("/generate_video_from_article", {
      script_id: scriptId,
    });
    return response.data;
  } catch (error) {
    console.error("Error generating video:", error);
    return {
      success: false,
      error:
        error.response?.data?.error ||
        "Could not connect to server. Video generation may take several minutes - please try again.",
      data: null,
    };
  }
};

export const generateVideoFromCustomText = async (title, text) => {
  if (USE_MOCK_API) {
    // Mock response for testing without backend
    await new Promise((resolve) => setTimeout(resolve, 4000)); // Simulate even longer processing
    return {
      success: true,
      data: {
        video_id: 101112,
        title: title,
        video_url:
          "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4", // Sample video URL
        vertical_video_url:
          "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4", // Same sample for vertical
        keywords: [
          "technology",
          "innovation",
          "science",
          "energy",
          "renewable",
        ],
      },
      error: null,
    };
  }

  try {
    const response = await videoGenAxios.post(
      "/generate_video_from_custom_text",
      {
        title,
        text,
      }
    );
    return response.data;
  } catch (error) {
    console.error("Error generating video from custom text:", error);
    return {
      success: false,
      error:
        error.response?.data?.error ||
        "Could not connect to server. Video generation may take several minutes - please try again.",
      data: null,
    };
  }
};

export const fetchVideos = async () => {
  if (USE_MOCK_API) {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      success: true,
      data: {
        videos: [
          {
            id: 1,
            title: "Sample Video 1",
            video_url:
              "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
            created_at: new Date().toISOString(),
          },
          {
            id: 2,
            title: "Sample Video 2",
            video_url:
              "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
            created_at: new Date(Date.now() - 86400000).toISOString(), // Yesterday
          },
        ],
      },
      error: null,
    };
  }

  try {
    const response = await axiosInstance.get("/videos");
    return response.data;
  } catch (error) {
    console.error("Error fetching videos:", error);
    return {
      success: false,
      error: error.response?.data?.error || "Failed to fetch videos",
    };
  }
};

export const getNewsArticles = fetchNewsArticles;

export default {
  fetchNewsArticles,
  getArticleById,
  generateScript,
  generateVideoFromArticle,
  generateVideoFromCustomText,
  fetchVideos,
};
