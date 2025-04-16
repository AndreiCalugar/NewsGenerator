# AutoVid

AutoVid is an automated video creation tool that generates news videos from text articles. It extracts keywords from news content, finds relevant stock footage, and creates a video with the news script.

## Features

- **News Aggregation**: Fetches news from various sources including GNews API and RSS feeds
- **Script Generation**: Uses AI to create engaging news scripts from article content
- **Keyword Extraction**: Automatically identifies relevant keywords from news articles
- **Video Creation**:
  - Downloads relevant stock footage from Pexels based on extracted keywords
  - Processes videos to a standardized format (1280x720)
  - Concatenates multiple clips into a single video (up to 30 seconds)
  - Each clip is trimmed to 6 seconds for consistent pacing
- **Database Integration**: Stores scripts and video metadata for easy retrieval
- **Clean User Interface**: Simple command-line interface for interacting with the system

## Requirements

- Python 3.7+
- FFmpeg (for video processing)
- OpenAI API key (for script generation)
- Pexels API key (for video footage)
- GNews API key (optional, for news fetching)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/AutoVid.git
   cd AutoVid
   ```

2. Install required packages:

   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:

   ```
   OPENAI_API_KEY=your_openai_api_key
   PEXELS_API_KEY=your_pexels_api_key
   GNEWS_API_KEY=your_gnews_api_key
   ```

4. Install FFmpeg:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

## Usage

Run the main script:

```
python AutoVid.py
```
