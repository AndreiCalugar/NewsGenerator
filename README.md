# AutoVid - Automated News Script Generator

AutoVid is a Python application that fetches top news from the United States using the GNews API (with RSS feeds as a fallback) and generates video scripts using OpenAI's GPT models.

## Features

- Fetch top headlines from the United States using GNews API
- Fallback to RSS feeds from popular US news sources if API fails
- Store news articles in a local SQLite database
- Generate video scripts for news articles using OpenAI's GPT models
- Extract keywords from articles and fetch relevant videos from Pexels API
- Create video edits by combining multiple clips based on the news content
- Interactive menu for script generation and management

## Prerequisites

- Python 3.7 or higher
- API keys for:
  - GNews API (https://gnews.io/)
  - OpenAI API (https://platform.openai.com/)
  - Pexels API (https://www.pexels.com/api/)
- FFmpeg installed for video editing capabilities

## Installation

1. Clone this repository:

   ```
   git clone <repository-url>
   cd autovid
   ```

2. Install required dependencies:

   ```
   pip install pandas requests python-dotenv openai feedparser moviepy
   ```

3. Create a `.env` file in the project root directory with your API keys:

   ```
   GNEWS_API_KEY=your_gnews_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   PEXELS_API_KEY=your_pexels_api_key_here
   ```

4. Install FFmpeg (required for video editing):
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Usage

Run the main script:

```
python AutoVid.py
```

### Program Flow

1. The program will first attempt to fetch news using the GNews API:

   - It will search for news about "United States"
   - If that fails, it will fetch top headlines from the US

2. If GNews API fails, it will fall back to RSS feeds from US news sources.

3. The fetched news articles will be stored in a local SQLite database.

4. You'll be presented with an interactive menu with the following options:

   - Generate script for a new article
   - Create video for an article
   - View recent scripts
   - View recent videos
   - Exit

5. When generating a script:

   - Select an article from the list of unused articles
   - The program will use OpenAI's GPT model to generate a script
   - You can review the script and choose to save it to the database

6. When creating a video:
   - Select an article with a generated script
   - The program will extract keywords from the article
   - Relevant videos will be fetched from Pexels API
   - A video edit will be created by combining clips with the script

## API Keys

### GNews API

- Sign up at https://gnews.io/
- Free tier provides 100 API calls per day
- Copy your API key to the `.env` file

### OpenAI API

- Sign up at https://platform.openai.com/
- Create an API key in your account settings
- Copy your API key to the `.env` file
- Note: OpenAI API usage incurs costs based on token usage

### Pexels API

- Sign up at https://www.pexels.com/api/
- Create an API key in your account settings
- Copy your API key to the `.env` file
- The provided key in your request (4IfcAeClimJMQWyPQJIvbK9VuIgGJ5JcyI9jC2o8NNxVAqZZQu5hAlsy) can be used

## Database

The application uses SQLite to store:

- News articles (title, description, source, URL, etc.)
- Generated scripts linked to their source articles
- Video metadata and paths to created videos

The database file (`news_database.db`) is created automatically in the project directory.

## Troubleshooting

- **API Key Issues**: Ensure your API keys are correctly set in the `.env` file

- **Network Errors**: Check your internet connection if API requests fail

- **Missing Modules**: Run `pip install <module_name>` if you encounter any missing module errors

- **MoviePy Installation Issues**:

  - For Python 3.13: `python -m pip install moviepy==1.0.3`
  - If you continue to have issues, the program will still run with limited functionality (downloading videos without editing)

- **Video Creation Errors**:

  - Make sure FFmpeg is properly installed and accessible in your PATH
  - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
  - Add the FFmpeg bin directory to your system PATH

- **Python Version Compatibility**:
  - This application works best with Python 3.7-3.11
  - If using Python 3.13, some features might be limited due to package compatibility

## License

MIT License
