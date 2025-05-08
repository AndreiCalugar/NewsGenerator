#!/bin/bash
# Install FFmpeg and required libraries
apt-get update
apt-get install -y ffmpeg espeak libespeak1 libespeak-dev

# Verify installations
echo "FFmpeg installation:"
ffmpeg -version | head -n 1

echo "Espeak installation:"
dpkg -l | grep espeak

# Create symlink in case of path issues
ln -sf /usr/lib/x86_64-linux-gnu/libespeak.so.1 /usr/lib/libespeak.so.1

echo "Libraries in /usr/lib:"
ls -la /usr/lib/libespeak*

echo "Libraries in /usr/lib/x86_64-linux-gnu:"
ls -la /usr/lib/x86_64-linux-gnu/libespeak*

# Continue with the regular build
# exit 0 