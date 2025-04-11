# AutoVid - Automated News Script Generator

AutoVid is a Python application that fetches top news from Romania using the GNews API (with RSS feeds as a fallback) and generates video scripts using OpenAI's GPT models.

## Features

- Fetch top headlines from Romania using GNews API
- Fallback to RSS feeds from popular Romanian news sources if API fails
- Store news articles in a local SQLite database
- Generate video scripts for news articles using OpenAI's GPT models
- Interactive menu for script generation and management

## Prerequisites

- Python 3.7 or higher
- API keys for:
  - GNews API (https://gnews.io/)
  - OpenAI API (https://platform.openai.com/)

## Installation

1. Clone this repository:

   ```
   git clone <repository-url>
   cd autovid
   ```

2. Install required dependencies:

   ```
   pip install pandas requests python-dotenv openai feedparser
   ```

3. Create a `.env` file in the project root directory with your API keys:
   ```
   GNEWS_API_KEY=your_gnews_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

Run the main script:
