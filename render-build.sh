#!/bin/bash
# Install FFmpeg
apt-get update && apt-get install -y ffmpeg libespeak1
echo "FFmpeg installed successfully"
python -c "import subprocess; print(subprocess.check_output(['which', 'ffmpeg']).decode().strip())"

# Also install libespeak which is needed for TTS functionality
echo "libespeak1 installed for TTS functionality"
# exit 0 