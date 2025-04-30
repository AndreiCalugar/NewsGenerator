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
        # Initialize with just output_dir parameter (which your class does accept)
        output_videos_dir = os.path.join(os.getcwd(), 'server', 'static', 'videos')
        os.makedirs(output_videos_dir, exist_ok=True)
        
        # Initialize with only parameters that your class supports
        video_creator = VideoCreator(output_dir=output_videos_dir)
        has_video_creator = True
        print(f"VideoCreator initialized successfully with output dir: {output_videos_dir}")
    except Exception as e:
        print(f"Error initializing VideoCreator: {e}")
        video_creator = None  # Ensure it's None if initialization fails
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
    try:
        data = request.get_json()
        script_id = data.get('script_id')
        
        if not script_id:
            return jsonify({"success": False, "error": "No script_id provided"}), 400
        
        # Debug info
        print(f"Starting video generation for script ID: {script_id}")
        
        # Get script details and article info
        db.cursor.execute("""
            SELECT s.id as script_id, s.script_text, s.article_id, 
                   a.title, a.description 
            FROM scripts s
            JOIN articles a ON s.article_id = a.id 
            WHERE s.id = ?
        """, (script_id,))
        
        script_data = db.cursor.fetchone()
        
        if not script_data:
            return jsonify({"success": False, "error": f"Script with ID {script_id} not found"}), 404
        
        # Generate a unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_filename = f"video_{script_id}_{timestamp}.mp4"
        video_path = os.path.join('static', 'videos', video_filename)
        
        if has_video_creator:
            try:
                # 1. Get the article title and description for keyword extraction
                article_title = script_data['title']
                article_description = script_data['description']
                script_text = script_data['script_text']
                
                # 2. Extract keywords - import needed components from AutoVid
                from AutoVid import KeywordExtractor, PexelsAPI
                import random
                
                print(f"Extracting keywords for: {article_title}")
                keyword_extractor = KeywordExtractor()
                keywords = keyword_extractor.extract_keywords(article_title, article_description)
                print(f"Initial keywords: {', '.join(keywords)}")
                
                # 3. Enhance keywords for video search
                article_category = "general"  # Simplified category detection
                enhanced_keywords = keyword_extractor.enhance_video_search(keywords, article_category)
                print(f"Enhanced keywords for video search: {', '.join(enhanced_keywords)}")
                
                # 4. Search for videos using keywords
                target_video_count = 5
                selected_videos_raw = []
                footage_pool_urls = set()
                
                print(f"\nSearching for up to {target_video_count} videos using keywords...")
                pexels_api = PexelsAPI()
                keywords_to_search = enhanced_keywords[:target_video_count]
                
                # 5. Search for each keyword
                for keyword in keywords_to_search:
                    if len(selected_videos_raw) >= target_video_count:
                        break
                        
                    print(f"Searching Pexels for videos with query: '{keyword}'...")
                    videos = pexels_api.search_videos(keyword, per_page=3)
                    
                    if videos:
                        print(f"Found {len(videos)} potential videos for '{keyword}'.")
                        video_added_for_keyword = False
                        for video_info in videos:
                            video_url = video_info.get('url')
                            
                            if video_url and video_url.endswith('.mp4'):
                                if video_url not in footage_pool_urls:
                                    print(f"  + Adding video for '{keyword}': {video_url}")
                                    selected_videos_raw.append({"url": video_url, "keyword": keyword})
                                    footage_pool_urls.add(video_url)
                                    video_added_for_keyword = True
                                    break
                        
                        if not video_added_for_keyword:
                            print(f"  - Could not find a suitable unique video for '{keyword}' from results.")
                    else:
                        print(f"No videos found for keyword '{keyword}'")
                
                # 6. Fallback to generic keywords if needed
                if len(selected_videos_raw) < target_video_count:
                    print(f"\nFound only {len(selected_videos_raw)} videos. Trying generic keywords...")
                    generic_keywords = ["news", "world", "city", "technology", "business", "people"]
                    random.shuffle(generic_keywords)
                    
                    for keyword in generic_keywords:
                        if len(selected_videos_raw) >= target_video_count:
                            break
                            
                        print(f"Searching Pexels for generic videos with query: '{keyword}'...")
                        videos = pexels_api.search_videos(keyword, per_page=3)
                        
                        if videos:
                            print(f"Found {len(videos)} potential generic videos for '{keyword}'.")
                            video_added_for_keyword = False
                            for video_info in videos:
                                video_url = video_info.get('url')
                                
                                if video_url and video_url.endswith('.mp4'):
                                    if video_url not in footage_pool_urls:
                                        print(f"  + Adding generic video for '{keyword}': {video_url}")
                                        selected_videos_raw.append({"url": video_url, "keyword": f"generic_{keyword}"})
                                        footage_pool_urls.add(video_url)
                                        video_added_for_keyword = True
                                        break
                            
                            if not video_added_for_keyword:
                                print(f"  - Could not find a suitable unique generic video for '{keyword}'.")
                        else:
                            print(f"No generic videos found for keyword '{keyword}'")
                
                # 7. Check if we have any videos
                if not selected_videos_raw:
                    print("\nError: Could not find any videos for the script.")
                    return jsonify({
                        "success": False,
                        "error": "Could not find any suitable videos for this script."
                    }), 500
                
                print(f"\nUsing {len(selected_videos_raw)} videos for the final video.")
                
                # 8. Create the video using the EXACT SAME parameter format as AutoVid.py
                print("\nCreating video...")
                # This time using the correct parameter format
                video_path = video_creator.create_video_with_narration(script_text, selected_videos_raw)
                
                if not video_path:
                    return jsonify({
                        "success": False,
                        "error": "Failed to create video. Check server logs for details."
                    }), 500
                
                # 9. Add video to database
                video_id = db.cursor.execute(
                    "INSERT INTO videos (script_id, video_path, created_at) VALUES (?, ?, datetime('now'))",
                    (script_id, video_path)
                ).lastrowid
                db.conn.commit()
                
                # 10. Return success with the video URL (properly formatted)
                video_url = f"/static/videos/{os.path.basename(video_path)}"
                print(f"Video created successfully at {video_path}, URL: {video_url}")
                
                return jsonify({
                    "success": True,
                    "data": {
                        "video_id": video_id,
                        "script_id": script_id,
                        "video_url": video_url,
                        "title": script_data['title']
                    },
                    "error": None
                })
                
            except Exception as e:
                print(f"Error in video creation process: {e}")
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "error": f"Video creation failed: {str(e)}"
                }), 500
        else:
            # Fallback if VideoCreator is not available
            print("VideoCreator not available. Creating placeholder video.")
            time.sleep(2)  # Simulate processing time
            
            # Create a placeholder file
            videos_dir = os.path.join(app.static_folder, 'videos')
            os.makedirs(videos_dir, exist_ok=True)
            placeholder_path = os.path.join(videos_dir, video_filename)
            with open(placeholder_path, 'wb') as f:
                f.write(b'placeholder')
            print(f"Created placeholder video at: {placeholder_path}")
            
            # Store video record in database
            db.cursor.execute(
                "INSERT INTO videos (script_id, video_path, created_at) VALUES (?, ?, datetime('now'))",
                (script_id, placeholder_path)
            )
            db.conn.commit()
            video_id = db.cursor.lastrowid
            
            # Return success with video URL
            video_url = f"/static/videos/{os.path.basename(placeholder_path)}"
            return jsonify({
                "success": True,
                "data": {
                    "video_id": video_id,
                    "script_id": script_id,
                    "video_url": video_url,
                    "title": script_data['title']
                },
                "error": None
            })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

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
            
            # Fix: Use a different variable name to avoid confusion
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
            
            # Get current timestamp for video ID
            video_id = int(current_time.strftime("%Y%m%d%H%M%S"))
            
            # Save to database
            db.cursor.execute(
                """
                INSERT INTO videos 
                (id, title, script_text, video_path, keywords, created_at) 
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    video_id,
                    title,
                    text_content,
                    placeholder_path,
                    ""  # No keywords for placeholder
                )
            )
            db.conn.commit()
            
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
        
        # If we have video_creator, continue with the original code
        data = request.json
        title = data.get('title')
        text_content = data.get('text')
        
        print(f"Generating video for custom text: {title}")
        
        # Use create_video_from_text which handles both regular and vertical videos
        result = video_creator.create_video_from_text(title, text_content)
        
        # Handle the various possible return types from create_video_from_text
        if isinstance(result, tuple):
            if len(result) == 2:
                video_path, error = result
                vertical_path = None
            else:
                video_path, error, vertical_path = result
                
            if error or not video_path or not os.path.exists(video_path):
                return jsonify({
                    "success": False,
                    "data": None,
                    "error": error or "Failed to create video"
                }), 500
        else:
            # Handle case where result is just the path
            video_path = result
            error = None
            vertical_path = None
        
        # Fix URL construction - directly use the basename of the file with correct path
        video_url = f"/static/videos/{os.path.basename(video_path)}"
        vertical_url = f"/static/videos/{os.path.basename(vertical_path)}" if vertical_path else None
        
        print(f"Video generated at: {video_path}, URL: {video_url}")
        if vertical_path:
            print(f"Vertical video generated at: {vertical_path}, URL: {vertical_url}")
        
        # Get keywords for reference
        from AutoVid import KeywordExtractor
        keyword_extractor = KeywordExtractor()
        keywords = keyword_extractor.extract_keywords(title, text_content)
        
        # Save to database
        current_time = datetime.now()
        video_id = int(current_time.strftime("%Y%m%d%H%M%S"))
        
        video_path_str = video_path
        if vertical_path:
            video_path_str = f"{video_path}|{vertical_path}"
            
        db.cursor.execute(
            """
            INSERT INTO videos 
            (id, title, script_text, video_path, keywords, created_at) 
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                video_id,
                title,
                text_content,
                video_path_str,
                ",".join(keywords) if keywords else ""
            )
        )
        db.conn.commit()
        
        return jsonify({
            "success": True,
            "data": {
                "video_id": video_id,
                "title": title,
                "video_url": video_url,
                "vertical_video_url": vertical_url,
                "keywords": keywords
            },
            "error": None
        })
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)