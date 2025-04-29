// client/src/services/api.js
import axios from "axios";

const API_URL = "http://localhost:5000/api";
// Set longer timeout for video generation requests (5 minutes)
const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 300000, // 5 minutes
});

// Use this flag to switch between mock and real API
const USE_MOCK_API = false;

export const generateScript = async (articleId) => {
  if (USE_MOCK_API) {
    // Mock response for testing without backend
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return {
      success: true,
      data: {
        script_id: 123,
        article_id: articleId,
        title: "Scientists Develop New Renewable Energy Technology",
        script:
          "Recent breakthroughs in renewable energy have scientists excited about a new potential power source. Researchers at MIT have developed a novel method to harness ambient thermal energy using specialized graphene-based materials. This technology could revolutionize how we power everyday devices, potentially eliminating the need for traditional batteries in many applications. Initial tests show the system can generate enough electricity to power small sensors and IoT devices indefinitely. While still in early development stages, researchers believe commercial applications could be available within five years.",
      },
      error: null,
    };
  }

  try {
    const response = await axios.post(`${API_URL}/generate_script`, {
      article_id: articleId,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: "Failed to connect to server" };
  }
};

export const generateVideoFromArticle = async (scriptId) => {
  if (USE_MOCK_API) {
    // Mock response for testing without backend
    await new Promise((resolve) => setTimeout(resolve, 3000)); // Simulate longer processing time
    return {
      success: true,
      data: {
        video_id: 789,
        title: "Scientists Discover New Renewable Energy Source",
        video_path:
          "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4", // Sample video URL
      },
      error: null,
    };
  }

  try {
    const response = await axiosInstance.post(`/generate_video_from_article`, {
      script_id: scriptId,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: "Failed to connect to server" };
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
    const response = await axios.post(
      `${API_URL}/generate_video_from_custom_text`,
      {
        title,
        text,
      }
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: "Failed to connect to server" };
  }
};

export const getNewsArticles = async () => {
  if (USE_MOCK_API) {
    // Mock response for testing without backend
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      success: true,
      data: {
        articles: [
          {
            id: 20250501,
            title: "Scientists Develop New Renewable Energy Technology",
            source: "Science Daily",
            description:
              "Researchers have developed a breakthrough technology that can convert ambient heat into electricity with unprecedented efficiency.",
          },
          {
            id: 20250502,
            title: "Global Economic Summit Addresses Climate Challenges",
            source: "Financial Times",
            description:
              "World leaders met in Geneva this week to address the economic implications of climate change and agree on collaborative approaches.",
          },
          {
            id: 20250503,
            title:
              "New AI System Can Diagnose Medical Conditions with 99% Accuracy",
            source: "Health Tech Today",
            description:
              "A groundbreaking artificial intelligence system has demonstrated the ability to diagnose a wide range of medical conditions with accuracy that surpasses human physicians.",
          },
        ],
      },
      error: null,
    };
  }

  try {
    const response = await axios.get(`${API_URL}/news_articles`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: "Failed to connect to server" };
  }
};
