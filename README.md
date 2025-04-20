# AutoVid News Generator

Automatically generate news videos from headlines. This tool fetches news headlines, generates scripts, and creates videos with narration.

## Features

- Fetches latest news headlines from GNews API
- Generates concise news scripts using OpenAI's GPT models
- Extracts keywords for relevant video footage
- Downloads appropriate video clips from Pexels
- Generates professional voice narration using multiple TTS options
- Combines video clips with narration to create complete news videos
- Organizes and tracks content in a SQLite database

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

## Usage

Run the main script to start the interactive menu:

```bash
python AutoVid.py
```

Follow the on-screen prompts to:

1. Generate scripts from news headlines
2. Create videos with narration
3. View existing scripts and videos

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

## License

[License information here]
