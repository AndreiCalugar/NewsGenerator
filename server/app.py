# server/app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sys
import traceback
import json
import sqlite3
from datetime import datetime
import time
import threading
import subprocess
import tempfile

# Import the specific classes we need from AutoVid
from AutoVid import ScriptGenerator
# Import GNewsAPI for fetching articles
from AutoVid import GNewsAPI
# Import pandas for DataFrame handling
import pandas as pd

# Add these lines to import the database class:
try:
    from AutoVid import SimpleDB  # Try to import the database class
except ImportError:
    # If SimpleDB isn't directly importable, we'll use our own implementation
    pass

try:
    from AutoVid import VideoCreator
    has_video_creator = True
    print("VideoCreator imported successfully")
except ImportError:
    has_video_creator = False
    print("VideoCreator not available - video generation will be limited")

# Set FFmpeg path automatically in production
if os.environ.get('RENDER'):
    # For Render deployment, FFmpeg is at this location
    os.environ['FFMPEG_BINARY'] = '/usr/bin/ffmpeg'

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://news-generator-5mtw.vercel.app",
    "https://text-to-video-generator-d10o20qok-andreicalugars-projects.vercel.app",
    "*"  # For development only - remove in production
]}})

# Setup static folders first
app_root = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(app_root, 'static')
static_videos_dir = os.path.join(static_dir, 'videos')

# Create necessary directories
os.makedirs(static_dir, exist_ok=True)
os.makedirs(static_videos_dir, exist_ok=True)
print(f"Static directory: {static_dir}")
print(f"Static videos directory: {static_videos_dir}")

# Configure paths and initialize components
script_generator = ScriptGenerator()

# Find where you set up static folder configuration
# Ensure static folders use absolute paths
app.config['STATIC_FOLDER'] = 'static'
os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'videos'), exist_ok=True)

# Add at the top after imports
print(f"Current working directory: {os.getcwd()}")
print(f"App file directory: {os.path.dirname(os.path.abspath(__file__))}")

# Database connection helper
class SimpleDB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        # Articles table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                source TEXT,
                description TEXT,
                content TEXT,
                published_at TIMESTAMP
            )
        """)
        
        # Scripts table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY,
                article_id INTEGER,
                script_text TEXT NOT NULL,
                created_at TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        """)
        
        # Videos table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                script_id INTEGER,
                video_path TEXT NOT NULL,
                created_at TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts (id)
            )
        """)
        
        # Commit the changes
        self.conn.commit()
        print("Database tables created if they didn't exist")
        
    def mark_article_as_used(self, article_id):
        # Implementation to mark article as used
        pass
        
    def add_script(self, article_id, script_text):
        # Implementation to add script
        self.cursor.execute(
            "INSERT INTO scripts (article_id, script_text, created_at) VALUES (?, ?, datetime('now'))",
            (article_id, script_text)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_unused_articles(self, limit=8):
        """Gets articles that haven't been used for videos yet."""
        # Use DISTINCT to avoid duplicates
        self.cursor.execute("""
            SELECT DISTINCT a.id, a.title, a.description, a.source 
            FROM articles a
            LEFT JOIN scripts s ON a.id = s.article_id
            LEFT JOIN videos v ON s.id = v.script_id
            WHERE s.id IS NULL OR v.id IS NULL
            ORDER BY a.id DESC
            LIMIT ?
        """, (limit,))
        
        return self.cursor.fetchall()

    def add_news_articles(self, articles_df):
        """Add news articles from DataFrame to database."""
        print(f"Adding {len(articles_df)} articles to database")
        added_ids = []
        
        for _, article in articles_df.iterrows():
            # Extract article data, with fallbacks for missing fields
            title = article.get('title', 'No Title')
            url = article.get('url', '')
            source = article.get('source', 'Unknown')
            description = article.get('description', '')
            content = article.get('content', description)
            
            # Generate a stable, reasonably sized ID for the article
            # Use the last 10 characters of URL hash to avoid massive integers
            url_hash = str(abs(hash(url)))[-10:] if url else str(abs(hash(title)))[-10:]
            article_id = int(url_hash)
            
            # Insert into database with explicit ID
            try:
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO articles 
                    (id, title, url, source, description, content, published_at) 
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (article_id, title, url, source, description, content)
                )
                
                added_ids.append(article_id)
                
            except Exception as e:
                print(f"Error inserting article '{title}': {e}")
        
        self.conn.commit()
        print(f"Added {len(added_ids)} articles to database")
        return added_ids

# Initialize DB
db = SimpleDB("news.db")

# Initialize GNewsAPI
try:
    news_api = GNewsAPI()
    print("GNewsAPI initialized successfully")
except Exception as e:
    print(f"Error initializing GNewsAPI: {e}")
    news_api = None

# Then initialize the VideoCreator:
if has_video_creator:
    try:
        # Render installs FFmpeg in /usr/bin/ffmpeg, so specify this path directly instead of prompting
        output_videos_dir = os.path.join(os.getcwd(), 'server', 'static', 'videos')
        os.makedirs(output_videos_dir, exist_ok=True)
        
        # Pass the FFmpeg path explicitly instead of prompting
        video_creator = VideoCreator(
            output_dir=output_videos_dir,
            ffmpeg_path='/usr/bin/ffmpeg'  # Specify this explicitly
        )
        has_video_creator = True
        print(f"VideoCreator initialized with explicit ffmpeg path: /usr/bin/ffmpeg")
    except Exception as e:
        print(f"Error initializing VideoCreator: {e}")
        video_creator = None
        has_video_creator = False
        print("VideoCreator not available - video generation will be limited")

@app.route('/api/news_articles', methods=['GET'])
def get_news_articles():
    try:
        if news_api is not None:
            # Use the same approach as in the CLI version
            print("Trying to fetch articles from GNewsAPI...")
            articles_df = pd.DataFrame()
            
            # First try searching for US news (matching CLI flow)
            try:
                print("Searching for US news...")
                us_news = news_api.search_news(query="United States", max_results=8)
                if not us_news.empty:
                    print(f"Found {len(us_news)} articles about US news")
                    articles_df = us_news
                else:
                    print("No results for US search, trying top headlines")
                    raise Exception("No results found for US search")
            except Exception as us_error:
                print(f"US news search failed: {us_error}")
                
                # Try top headlines instead (matching CLI flow)
                try:
                    print("Fetching top headlines...")
                    headlines = news_api.get_top_headlines(country="us", max_results=8)
                    if not headlines.empty:
                        print(f"Found {len(headlines)} top headlines")
                        articles_df = headlines
                    else:
                        print("No headlines found")
                except Exception as headlines_error:
                    print(f"Headlines fetch failed: {headlines_error}")
            
            # Format articles for frontend
            if not articles_df.empty:
                articles = []
                # First, add articles to database to get proper IDs
                try:
                    # Store in database for future use
                    article_ids = db.add_news_articles(articles_df)
                except Exception as e:
                    print(f"Error storing articles in database: {e}")
                    article_ids = []
                
                for i, (_, article) in enumerate(articles_df.iterrows()):
                    url = article.get('url', '')
                    title = article.get('title', 'No Title')
                    
                    # Generate a consistent ID the same way we do when storing in DB
                    url_hash = str(abs(hash(url)))[-10:] if url else str(abs(hash(title)))[-10:]
                    article_id = int(url_hash)
                    
                    # Use the generated ID or database-assigned ID
                    id_to_use = article_ids[i] if i < len(article_ids) else article_id
                    
                    articles.append({
                        "id": id_to_use,
                        "title": title,
                        "description": article.get('description', 'No description available'),
                        "source": article.get('source', 'Unknown Source')
                    })
                
                source_info = "GNewsAPI (Live)"
                print(f"Returning {len(articles)} articles from GNewsAPI")
                return jsonify({
                    "success": True,
                    "data": {
                        "articles": articles,
                        "source_info": source_info
                    },
                    "error": None
                })
        
        # Fallback to database if GNewsAPI isn't available or returned no results
        print("GNewsAPI not available or returned no results, falling back to database...")
        unused_articles = db.get_unused_articles(limit=8)
        
        if not unused_articles:
            return jsonify({
                "success": False, 
                "error": "No articles available. Please try again later."
            })
        
        # Format articles from the database
        articles = []
        for article_id, title, description, source in unused_articles:
            articles.append({
                "id": article_id,
                "title": title,
                "description": description,
                "source": source
            })
        
        source_info = "Database (SimpleDB)"
        print(f"Returning {len(articles)} articles from database")
        
        return jsonify({
            "success": True,
            "data": {
                "articles": articles,
                "source_info": source_info
            },
            "error": None
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate_script', methods=['POST'])
def generate_script():
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({"success": False, "error": "No article_id provided"}), 400
        
        # Convert to integer if needed
        try:
            article_id = int(article_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": f"Invalid article ID format: {article_id}"}), 400
            
        # Debug info
        print(f"Generating script for article ID: {article_id}")
        
        # Get article details
        db.cursor.execute(
            "SELECT id, title, description FROM articles WHERE id = ?", 
            (article_id,)
        )
        article = db.cursor.fetchone()
        
        if not article:
            # Try to debug
            db.cursor.execute("SELECT id FROM articles")
            available_ids = [row[0] for row in db.cursor.fetchall()]
            print(f"Available article IDs: {available_ids}")
            
            return jsonify({
                "success": False, 
                "error": f"Article with ID {article_id} not found"
            }), 404
            
        # Generate script using the same function as in CLI
        script = script_generator.generate_script(article['title'], article['description'])
        
        # Save script to database
        script_id = db.add_script(article_id, script)
        db.mark_article_as_used(article_id)
        
        return jsonify({
            "success": True,
            "data": {
                "script_id": script_id,
                "article_id": article_id,
                "title": article['title'],
                "script": script
            },
            "error": None
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate_video_from_article', methods=['POST'])
def generate_video_from_article():
    """Generate a video for a script"""
    try:
        data = request.json
        script_id = data.get('script_id')
        
        if not script_id:
            return jsonify({"success": False, "error": "No script_id provided"}), 400
        
        # Debug info
        print(f"Starting video generation for script ID: {script_id}")
        
        # Get script from database
        db.cursor.execute(
            """
            SELECT s.id, s.script_text, a.title 
            FROM scripts s
            JOIN articles a ON s.article_id = a.id
            WHERE s.id = ?
            """, 
            (script_id,)
        )
        script_data = db.cursor.fetchone()
        
        if not script_data:
            return jsonify({"success": False, "error": f"Script with ID {script_id} not found"}), 404
            
        # Create a unique video filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"video_{script_id}_{timestamp}.mp4"
        videos_dir = os.path.join(os.getcwd(), 'server', 'static', 'videos')
        video_path = os.path.join(videos_dir, video_filename)
        
        # Start video generation in background thread
        def generate_video_in_background():
            try:
                print(f"[BG THREAD] Starting video generation for: {script_data['title']}")
                print(f"[BG THREAD] Using script with {len(script_data['script_text'])} characters")
                
                # ... existing monitoring code ...
                
                # This is the line that gets the result
                video_result = video_creator.create_video_from_text(
                    script_data['title'], 
                    script_data['script_text']
                )
                
                print(f"[BG THREAD] Video generation completed: {video_result}")
                
                # Fix for tuple result - extract the main video path
                if isinstance(video_result, tuple):
                    video_path = video_result[0]  # Get just the main video path
                else:
                    video_path = video_result
                
                # Save to database if successful
                if video_path:
                    db.cursor.execute(
                        "INSERT INTO videos (script_id, video_path, created_at) VALUES (?, ?, datetime('now'))",
                        (script_id, video_path)
                    )
                    db.conn.commit()
                    print(f"[BG THREAD] Video saved to database: {video_path}")
                
            except Exception as e:
                print(f"[BG THREAD] Error creating video: {e}")
                traceback.print_exc()
                
        thread = threading.Thread(target=generate_video_in_background)
        thread.daemon = True
        thread.start()
        
        # Return immediate response
        return jsonify({
            "success": True,
            "data": {
                "status": "processing",
                "message": "Video generation started"
            }
        })
        
    except Exception as e:
        print(f"Error in generate_video_from_article: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

def create_text_video(title, text, output_path):
    """Create a very simple video with text using ffmpeg"""
    try:
        print(f"Creating text video at: {output_path}")
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a basic image with text
            image_path = os.path.join(temp_dir, "text.png")
            
            # Use ffmpeg to create image with text
            text_cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'color=c=black:s=1280x720:d=10',
                '-vf', f'drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text={title}\\n\\n{text}:fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10',
                '-t', '10',
                output_path
            ]
            
            subprocess.run(text_cmd, check=True)
            print(f"Created simple text video at: {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Error creating text video: {e}")
        traceback.print_exc()
        return None

@app.route('/api/videos', methods=['GET'])
def get_videos():
    try:
        # Get all videos ordered by created_at descending (newest first)
        db.cursor.execute("""
            SELECT v.id, v.script_id, v.video_path, v.created_at, 
                   s.article_id, a.title
            FROM videos v
            JOIN scripts s ON v.script_id = s.id
            JOIN articles a ON s.article_id = a.id
            ORDER BY v.created_at DESC
            LIMIT 50
        """)
        
        videos_raw = db.cursor.fetchall()
        
        videos = []
        for video in videos_raw:
            videos.append({
                "id": video[0],
                "script_id": video[1],
                "video_url": f"/static/{video[2]}" if not video[2].startswith('/static/') else video[2],
                "created_at": video[3],
                "article_id": video[4],
                "title": video[5]
            })
        
        return jsonify({
            "success": True,
            "data": {
                "videos": videos
            },
            "error": None
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate_video_from_custom_text', methods=['POST'])
def generate_video_from_custom_text():
    try:
        # Check if video_creator is available
        if not has_video_creator or video_creator is None:
            print("VideoCreator not available. Creating placeholder text-to-video.")
            
            # Create a placeholder response
            data = request.json
            title = data.get('title', 'Untitled')
            text_content = data.get('text', '')
            
            # Fix: Use a different variable n
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y%m%d_%H%M%S')
            video_filename = f"custom_video_{timestamp}.mp4"
            
            # Create placeholder file
            videos_dir = os.path.join(app.static_folder, 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            placeholder_path = os.path.join(videos_dir, video_filename)
            
            with open(placeholder_path, 'wb') as f:
                f.write(b'placeholder')
            print(f"Created placeholder video at: {placeholder_path}")
            
            # Construct the relative URL for the frontend
            video_url = f"/static/videos/{os.path.basename(placeholder_path)}"
            
            # FIX: Save to database using only columns that actually exist
            db.cursor.execute(
                """
                INSERT INTO videos 
                (script_id, video_path, created_at) 
                VALUES (?, ?, datetime('now'))
                """,
                (
                    0,  # Use 0 as a placeholder for script_id
                    placeholder_path
                )
            )
            db.conn.commit()
            video_id = db.cursor.lastrowid  # Get the auto-generated ID
            
            return jsonify({
                "success": True,
                "data": {
                    "video_id": video_id,
                    "title": title,
                    "video_url": video_url,
                    "vertical_video_url": None,
                    "message": "Created placeholder video (full generation not available)"
                },
                "error": None
            })
        
        # Rest of your code for the case when video_creator is available...
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "data": None,
            "error": str(e)
        }), 500

@app.route('/test')
def test_page():
    return render_template('test.html')

@app.route('/api/health', methods=['GET', 'HEAD'])
def health_check():
    return jsonify({"status": "ok", "message": "Server is running"}), 200

@app.route('/videos/<path:filename>')
def serve_video(filename):
    video_path = os.path.join(os.path.dirname(__file__), 'static', 'videos')
    return send_from_directory(video_path, filename)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    return jsonify({
        "status": "ok",
        "message": "API is running. Use /api/... endpoints to access functionality.",
        "version": "1.0.0",
        "documentation": "Contact developer for API documentation"
    })

@app.route('/api/video_status/<int:script_id>', methods=['GET'])
def get_video_status(script_id):
    """Check if a video has been generated for a script"""
    try:
        # Look for video in database
        db.cursor.execute(
            "SELECT id, video_path, created_at FROM videos WHERE script_id = ? ORDER BY created_at DESC LIMIT 1", 
            (script_id,)
        )
        
        video = db.cursor.fetchone()
        
        if video:
            video_path = video['video_path']
            # Check if file exists and has content
            full_path = os.path.join(os.getcwd(), 'server', video_path.lstrip('/')) if video_path.startswith('/') else video_path
            
            if os.path.exists(full_path) and os.path.getsize(full_path) > 1000:  # Real video should be > 1KB
                # Video is ready
                return jsonify({
                    "success": True,
                    "data": {
                        "status": "completed",
                        "video_id": video['id'],
                        "video_url": f"/static/{os.path.basename(video_path)}" if not video_path.startswith('/static/') else video_path,
                        "created_at": video['created_at']
                    },
                    "error": None
                })
            else:
                # Video is a placeholder or still processing
                return jsonify({
                    "success": True,
                    "data": {
                        "status": "processing",
                        "message": "Video is still being generated. Please check again in a minute."
                    },
                    "error": None
                })
        else:
            # No video found
            return jsonify({
                "success": True,
                "data": {
                    "status": "not_found",
                    "message": "No video found for this script. You may need to request video generation."
                },
                "error": None
            })
            
    except Exception as e:
        print(f"Error checking video status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/debug/fonts', methods=['GET'])
def debug_fonts():
    """List available fonts on the system"""
    try:
        result = subprocess.run(['find', '/', '-name', '*.ttf', '-o', '-name', '*.TTF'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        fonts = result.stdout.decode('utf-8').split('\n')
        return jsonify({"available_fonts": fonts})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/create_test_video', methods=['GET'])
def create_test_video():
    """Create a test video to verify ffmpeg works"""
    try:
        output_dir = os.path.join(os.getcwd(), 'server', 'static', 'videos')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"test_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        # Super simple command to generate a 5-second video
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'color=c=blue:s=640x360:d=5',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            video_url = f"/static/videos/{os.path.basename(output_path)}"
            return jsonify({
                "success": True, 
                "message": "Test video created", 
                "video_url": video_url
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Failed to create test video: {result.stderr.decode('utf-8')}"
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)