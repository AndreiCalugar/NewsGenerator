# AutoVid News Generator

AutoVid is an automated video creation tool that converts news articles and custom text into professional-looking videos with narration.

## Features

- **News Aggregation**: Fetches current news articles from various online sources
- **Script Generation**: Converts news articles into concise, engaging scripts
- **Keyword Extraction**: Identifies key topics to find relevant video footage
- **Video Creation**:
  - Downloads stock footage based on keywords
  - Generates speech narration from scripts
  - Creates professional videos with narration and footage
  - Produces both standard (16:9) and vertical (9:16) versions for social media
- **Direct Text-to-Video**: Convert any custom text directly into a video
- **Database Management**: Stores articles, scripts, and video information
- **Simple Interface**: Easy-to-use command-line interface
- **Web Interface**: Web interface with API endpoints for integration

## Installation

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your API keys in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_key
   GNEWS_API_KEY=your_gnews_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   PEXELS_API_KEY=your_pexels_key
   ```

## Usage

Run the main script to access all features:

```
python AutoVid.py
```

### Main Menu Options

1. **Generate script for a new article**: Select news articles and create scripts
2. **Download videos for an article**: Create videos from existing scripts
3. **View recent scripts**: Browse and manage previously generated scripts
4. **View recent videos**: Browse and manage created videos
5. **Create video from custom text**: Generate a video directly from any text input
6. **Exit**: Close the application

### Web Interface & API

AutoVid now includes a web server with API endpoints for integration with other applications:

1. Start the server:
   ```
   python server/app.py
   ```
2. Access the web interface at `http://localhost:5000`

#### API Endpoints

- **POST /api/generate_script**: Fetches news and generates a script
- **POST /api/generate_video_from_article**: Creates a video from a saved script
- **POST /api/generate_video_from_custom_text**: Creates a video directly from custom text

Example API usage:

```javascript
// Generate video from custom text
fetch("http://localhost:5000/api/generate_video_from_custom_text", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "My Custom Video",
    text: "This is the content for my video...",
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### Creating Video from Custom Text

The text-to-video feature allows you to generate videos from any text:

1. Select option 5 from the main menu (CLI) or use the web interface
2. Enter a title for your video
3. Type or paste your custom text
4. Confirm the creation process
5. The system will:
   - Generate a script from your text
   - Extract keywords
   - Download relevant stock footage
   - Create narration audio
   - Produce both standard and vertical videos

Videos will be saved in the `videos/text2video_[timestamp]` directory (CLI) or `static/videos` (web server) and added to the database for future reference.

## Requirements

- Python 3.8+
- FFmpeg (must be installed and in your PATH)
- API keys for OpenAI, GNews, ElevenLabs, and Pexels
- Internet connection for downloading news and videos
- Flask and Flask-CORS (for web server functionality)

## Limitations

1. Video quality depends on available stock footage matching your keywords
2. The script generation is limited by the capabilities of the AI model
3. The script text is properly formatted without special characters that might cause FFmpeg command issues

## License

[License information here]

## Speech Generation

The system uses a tiered approach to text-to-speech (TTS) generation:

1. **Primary: ElevenLabs** - High-quality, natural-sounding voices (requires API key)

   - Used for professional news narration when available
   - Configurable voice selection (default: "Donavan")
   - Supports multiple languages and accents

2. **Fallback 1: pyttsx3** - Offline TTS engine

   - Used when ElevenLabs is unavailable or fails
   - No internet connection or API key required
   - Limited voice quality compared to online options

3. **Fallback 2: Google Text-to-Speech (gTTS)**
   - Used when both ElevenLabs and pyttsx3 fail
   - Requires internet connection but no API key
   - Decent quality but limited customization

This multi-tiered approach ensures the system can continue to function even if premium services are unavailable.

## Setup and Installation

1. Clone the repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GNEWS_API_KEY=your_gnews_api_key
   PEXELS_API_KEY=your_pexels_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   ```
4. Ensure FFmpeg is installed on your system
5. (Optional) Install MoviePy for enhanced video creation:
   ```
   pip install moviepy
   ```

## Dependencies

- Python 3.8+
- OpenAI API
- GNews API
- Pexels API
- ElevenLabs API (optional but recommended for best quality)
- FFmpeg
- MoviePy (optional)
- pyttsx3
- gTTS
- Flask and Flask-CORS (for web server)
- SQLite (for database)

## License

[License information here]

## Feature: Video Subtitles

The application supports automatic subtitle generation and display for created videos:

### Subtitle Generation and Display

- **Automatic Transcription**: Uses OpenAI's Whisper model to transcribe the narration audio
- **Multi-approach Subtitle Display**: Implements several methods to ensure subtitles work across different environments:
  1. **Traditional Subtitle Burning**: Attempts to embed ASS format subtitles using FFmpeg filters
  2. **Sequential Caption Overlays**: Creates a series of video segments with synchronized text captions
  3. **Fixed Caption Fallback**: If other methods fail, displays a simplified caption with key content

### How It Works

1. The narration audio is transcribed using Whisper, which generates timestamps and text segments
2. The system first attempts to use traditional subtitle filters with the ASS format
3. If that fails, it uses a sequential captioning approach that adds text overlays to each segment of the video
4. As a final fallback, a simplified caption containing the beginning of the script is added

## API Endpoints

- `GET /api/news_articles` - Get latest news articles
- `POST /api/generate_script` - Generate script from an article
- `POST /api/generate_video_from_article` - Create video from a script
- `POST /api/generate_video_from_custom_text` - Create video from custom text
- `GET /api/videos` - Get all generated videos
- `GET /api/health` - Check API health status

### Technical Implementation

- **Whisper Integration**: Transcribes speech to text with precise timestamps
- **FFmpeg Text Filters**: Uses drawtext filters to overlay captions at specific timestamps
- **Multi-segment Processing**: Divides video into segments with appropriate captions for each part
- **Robust Error Handling**: Multiple fallback approaches ensure videos always have some form of captioning

### Troubleshooting

If subtitles are not displaying correctly, check:

1. The FFmpeg installation is complete with all required codecs
2. The video output is being created successfully before subtitle application
3. The script text is properly formatted without special characters that might cause FFmpeg command issues
