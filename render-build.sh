#!/bin/bash
# Install FFmpeg
apt-get update && apt-get install -y ffmpeg
echo "FFmpeg installed successfully"
python -c "import subprocess; print(subprocess.check_output(['which', 'ffmpeg']).decode().strip())"
# Continue with the regular build
# exit 0 