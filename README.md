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

## New Feature: Video Subtitles

The application now supports automatic subtitle generation and display for created videos:

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

### Technical Implementation

- **Whisper Integration**: Transcribes speech to text with precise timestamps
- **FFmpeg Text Filters**: Uses drawtext filters to overlay captions at specific timestamps
- **Multi-segment Processing**: Divides video into segments with appropriate captions for each part
- **Robust Error Handling**: Multiple fallback approaches ensure videos always have some form of captioning

### Requirements

- FFmpeg with libx264 support
- OpenAI Whisper (optional, but required for transcription)
- Python 3.9+ with the dependencies listed in requirements.txt

### Troubleshooting

If subtitles are not displaying correctly, check:

1. The FFmpeg installation is complete with all required codecs
2. The video output is being created successfully before subtitle application
3. The script text is properly formatted without special characters that might cause FFmpeg command issues
