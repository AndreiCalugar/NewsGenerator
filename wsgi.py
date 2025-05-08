import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.abspath("./server"))

from app import app

# This timeout configuration will be used by Render
# Increase the timeout to 5 minutes (300 seconds)
timeout = 300
workers = 2
threads = 2

if __name__ == "__main__":
    app.run() 