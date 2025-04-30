import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.abspath("./server"))

from app import app

if __name__ == "__main__":
    app.run() 