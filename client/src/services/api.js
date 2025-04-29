// client/src/services/api.js
import axios from "axios";

const API_URL = "http://localhost:5000/api";

// Use this flag to switch between mock and real API
const USE_MOCK_API = false;

export const generateScript = async () => {
  if (USE_MOCK_API) {
    // Mock response for testing without backend
    await new Promise((resolve) => setTimeout(resolve, 1500)); // Simulate network delay
    return {
      success: true,
      data: {
        script_id: 123,
        article_id: 456,
        title: "Scientists Discover New Renewable Energy Source",
        script:
          "Recent breakthroughs in renewable energy have scientists excited about a new potential power source. Researchers at MIT have developed a novel method to harness ambient thermal energy using specialized graphene-based materials. This technology could revolutionize how we power everyday devices, potentially eliminating the need for traditional batteries in many applications. Initial tests show the system can generate enough electricity to power small sensors and IoT devices indefinitely. While still in early development stages, researchers believe commercial applications could be available within five years.",
      },
      error: null,
    };
  }

  try {
    const response = await axios.post(`${API_URL}/generate_script`);
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
    const response = await axios.post(
      `${API_URL}/generate_video_from_article`,
      {
        script_id: scriptId,
      }
    );
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
