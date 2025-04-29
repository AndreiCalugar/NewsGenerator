# server/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import sqlite3
import traceback
import json
from datetime import datetime

# First, try to import what we can from AutoVid
# We'll create fallbacks for anything we can't import
available_classes = {}
try:
    # Try to import all the required classes
    from AutoVid import VideoCreator
    available_classes['VideoCreator'] = VideoCreator
except ImportError:
    print("Warning: VideoCreator not available")

try:
    from AutoVid import ScriptGenerator
    available_classes['ScriptGenerator'] = ScriptGenerator
except ImportError:
    print("Warning: ScriptGenerator not available")

try:
    from AutoVid import KeywordExtractor
    available_classes['KeywordExtractor'] = KeywordExtractor
except ImportError:
    print("Warning: KeywordExtractor not available")

try:
    from AutoVid import PexelsAPI
    available_classes['PexelsAPI'] = PexelsAPI
except ImportError:
    print("Warning: PexelsAPI not available")

# Try to find database class - it might have several different names
db_class = None
try:
    from AutoVid import ThreadSafeDB
    db_class = ThreadSafeDB
except ImportError:
    try:
        from AutoVid import Database
        db_class = Database
    except ImportError:
        try:
            from AutoVid import DBConnection
            db_class = DBConnection
        except ImportError:
            try:
                from AutoVid import SQLiteDB
                db_class = SQLiteDB
            except ImportError:
                # Create a simple database class as fallback
                class SimpleDB:
                    def __init__(self, db_path):
                        self.db_path = db_path
                        self.conn = sqlite3.connect(db_path, check_same_thread=False)
                        self.conn.row_factory = sqlite3.Row
                        self.cursor = self.conn.cursor()
                        print(f"SimpleDB: Connected to {db_path}")
                    
                    def _create_tables(self):
                        print("SimpleDB: Creating tables if they don't exist")
                        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS articles (
                                id INTEGER PRIMARY KEY,
                                title TEXT NOT NULL,
                                url TEXT,
                                source TEXT,
                                description TEXT,
                                content TEXT,
                                published_at TEXT
                            )
                        """)
                        
                        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS scripts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                article_id INTEGER,
                                script_text TEXT NOT NULL,
                                created_at TEXT,
                                FOREIGN KEY (article_id) REFERENCES articles (id)
                            )
                        """)
                        
                        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS videos (
                                id INTEGER PRIMARY KEY,
                                script_id INTEGER,
                                title TEXT,
                                script_text TEXT,
                                video_path TEXT,
                                keywords TEXT,
                                created_at TEXT,
                                FOREIGN KEY (script_id) REFERENCES scripts (id)
                            )
                        """)
                        
                        self.conn.commit()
                        return True
                        
                    def close(self):
                        if self.conn:
                            self.conn.close()
                            print(f"SimpleDB: Connection to {self.db_path} closed")
                
                db_class = SimpleDB
                print("Using SimpleDB fallback for database operations")

# Try to find the news fetcher class - it might have several different names
news_fetcher_class = None
try:
    from AutoVid import NewsFetcher
    news_fetcher_class = NewsFetcher
except ImportError:
    try:
        from AutoVid import NewsScraper
        news_fetcher_class = NewsScraper
    except ImportError:
        try:
            from AutoVid import NewsAPI
            news_fetcher_class = NewsAPI
        except ImportError:
            # Create a simple news fetcher as fallback
            class DummyNewsFetcher:
                def __init__(self, db):
                    self.db = db
                    
                    # List of realistic dummy articles
                    self.dummy_articles = [
                        {
                            "id": 20250501,
                            "title": "Scientists Develop New Renewable Energy Technology",
                            "url": "https://example.com/renewable-energy",
                            "source": "Science Daily",
                            "description": "Researchers have developed a breakthrough technology that can convert ambient heat into electricity with unprecedented efficiency, potentially revolutionizing how we power everyday devices.",
                            "content": "A team of researchers from MIT and Stanford have developed a revolutionary new technology that can convert ambient thermal energy into electricity with unprecedented efficiency. The new system uses specially engineered nanomaterials that can harvest heat from their surroundings and transform it into usable electric power. In early tests, the system has shown the ability to generate enough electricity to power small sensors and IoT devices indefinitely, without requiring batteries or other external power sources. 'This could fundamentally change how we think about powering small electronic devices,' said lead researcher Dr. Emily Chen. The team believes that within five years, the technology could be scaled to power larger devices and eventually contribute to the renewable energy grid.",
                        },
                        {
                            "id": 20250502,
                            "title": "Global Economic Summit Addresses Climate Challenges",
                            "url": "https://example.com/economic-summit",
                            "source": "Financial Times",
                            "description": "World leaders met in Geneva this week to address the economic implications of climate change and agree on collaborative approaches to sustainable development.",
                            "content": "Representatives from over 40 countries gathered in Geneva this week for the annual Global Economic Summit, with climate change taking center stage in the discussions. The three-day conference focused on creating financial incentives for green technology development and implementation of carbon reduction strategies across various industries. 'We must balance economic growth with environmental responsibility,' stated UN Secretary-General in the opening address. The summit concluded with a joint commitment to increase climate finance by $100 billion annually by 2030, with particular focus on supporting developing nations in their transition to clean energy infrastructure. Market analysts noted that the announcements had immediate impact on renewable energy stocks, with several major green tech companies seeing significant gains following the news.",
                        },
                        {
                            "id": 20250503,
                            "title": "New AI System Can Diagnose Medical Conditions with 99% Accuracy",
                            "url": "https://example.com/ai-medical-diagnosis",
                            "source": "Health Tech Today",
                            "description": "A groundbreaking artificial intelligence system has demonstrated the ability to diagnose a wide range of medical conditions with accuracy that surpasses human physicians.",
                            "content": "Healthcare technology company Medscan announced today the results of a three-year clinical trial of their advanced diagnostic AI system, showing it can identify over 200 different medical conditions with 99.1% accuracy. The system, which analyzes patient data including symptoms, medical history, lab results, and imaging, outperformed human physicians who averaged 91.5% accuracy on the same cases. 'This represents a significant advance in how we can support healthcare providers in making quick, accurate diagnoses,' said Medscan CEO Sarah Johnson. The system is now being implemented in 12 major hospitals across the country, with plans for wider rollout next year. Medical ethicists have noted that while the technology shows promise, it should complement rather than replace physician judgment. 'The human element remains crucial in patient care,' commented Dr. Robert Park, a medical ethics specialist not involved with the development.",
                        }
                    ]
                
                def fetch_top_headlines(self):
                    print("Using dummy news fetcher - inserting realistic test articles")
                    
                    # Clear existing articles (optional)
                    try:
                        self.db.cursor.execute("DELETE FROM articles")
                        self.db.conn.commit()
                    except:
                        pass  # If table doesn't exist yet
                    
                    # Insert the dummy articles
                    for article in self.dummy_articles:
                        self.db.cursor.execute(
                            """
                            INSERT OR REPLACE INTO articles 
                            (id, title, url, source, description, content, published_at) 
                            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                            """,
                            (
                                article["id"],
                                article["title"],
                                article["url"],
                                article["source"],
                                article["description"],
                                article["content"],
                            )
                        )
                    
                    self.db.conn.commit()
                    print(f"Inserted {len(self.dummy_articles)} dummy articles into database")
                    return True
            
            news_fetcher_class = DummyNewsFetcher
            print("Using DummyNewsFetcher for news fetching")

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configure static folder for serving videos
app.config['STATIC_FOLDER'] = 'static'
os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'videos'), exist_ok=True)

# Initialize components with our discovered or fallback classes
print("Initializing components...")
db = db_class("news.db")
db._create_tables()

# Initialize remaining components - handle missing classes
video_creator = available_classes.get('VideoCreator', lambda **kwargs: None)(output_dir="static/videos")
news_fetcher = news_fetcher_class(db)
script_generator = available_classes.get('ScriptGenerator', lambda: None)()
keyword_extractor = available_classes.get('KeywordExtractor', lambda: None)()
pexels_api = available_classes.get('PexelsAPI', lambda: None)()

print("App initialization complete")

os.environ['DISABLE_SUBTITLES'] = '1'  # Temporarily disable subtitles

@app.route('/api/news_articles', methods=['GET'])
def get_news_articles():
    try:
        # Fetch news headlines first (ensure we have latest news)
        news_fetcher.fetch_top_headlines()
        
        # Get the latest headlines from database
        db.cursor.execute("""
            SELECT id, title, url, source, description 
            FROM articles 
            ORDER BY id DESC 
            LIMIT 10
        """)
        articles_raw = db.cursor.fetchall()
        
        if not articles_raw:
            return jsonify({
                "success": False,
                "data": None,
                "error": "No articles found"
            })
        
        # Format articles for the frontend
        articles = []
        for article in articles_raw:
            articles.append({
                "id": article[0],
                "title": article[1],
                "url": article[2],
                "source": article[3],
                "description": article[4]
            })
            
        return jsonify({
            "success": True,
            "data": {
                "articles": articles
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

@app.route('/api/generate_script', methods=['POST'])
def generate_script():
    try:
        # Get article_id from request
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({
                "success": False,
                "data": None,
                "error": "No article_id provided"
            }), 400
        
        # Get the article from the database
        db.cursor.execute("""
            SELECT id, title, url, source, description 
            FROM articles 
            WHERE id = ?
        """, (article_id,))
        article = db.cursor.fetchone()
        
        if not article:
            return jsonify({
                "success": False,
                "data": None,
                "error": f"Article with ID {article_id} not found"
            }), 404
            
        article_id = article[0]
        article_title = article[1]
        article_desc = article[4]
        
        # Generate script using the existing script generator
        script = script_generator.generate_script(article_title, article_desc)
        
        if not script:
            return jsonify({
                "success": False,
                "data": None,
                "error": "Failed to generate script"
            })
            
        # Save script to database
        db.cursor.execute(
            """
            INSERT INTO scripts (article_id, script_text, created_at)
            VALUES (?, ?, datetime('now'))
            """,
            (article_id, script)
        )
        db.conn.commit()
        script_id = db.cursor.lastrowid
        
        # Return the script data
        return jsonify({
            "success": True,
            "data": {
                "script_id": script_id,
                "article_id": article_id,
                "title": article_title,
                "script": script
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

@app.route('/api/generate_video_from_article', methods=['POST'])
def generate_video_from_article():
    try:
        data = request.json
        script_id = data.get('script_id')
        
        if not script_id:
            return jsonify({
                "success": False,
                "data": None,
                "error": "Script ID is required"
            }), 400
            
        # Get the script from database
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
            return jsonify({
                "success": False,
                "data": None,
                "error": "Script not found"
            }), 404
            
        script_id, script_text, title = script_data
        
        # Extract keywords from script
        keywords = keyword_extractor.extract_keywords(title, script_text)
        
        # Create video from script
        selected_videos_raw = []
        
        # Handle keyword search and video downloads
        for keyword in keywords[:5]:  # Limit to 5 keywords
            videos = pexels_api.search_videos(keyword, per_page=3)
            if videos:
                for video in videos[:1]:  # Get just the first video per keyword
                    video_url = video.get('url')
                    if video_url and video_url not in [v.get('url') for v in selected_videos_raw]:
                        selected_videos_raw.append({
                            "url": video_url,
                            "keyword": keyword
                        })
                        break
        
        # Generate video with narration
        try:
            # Make subtitle generation optional and catch errors
            try:
                if os.environ.get('DISABLE_SUBTITLES') != '1':
                    print("Generating subtitles (can be disabled with DISABLE_SUBTITLES=1)...")
                    # subtitle generation code
                else:
                    print("Subtitle generation is disabled")
            except Exception as subtitle_error:
                print(f"Subtitle generation failed but continuing: {subtitle_error}")
            
            # Continue with the rest of the video creation process
            final_video = video_creator.create_video_with_narration(script_text, selected_videos_raw)
            
            if not final_video or not os.path.exists(final_video):
                return jsonify({
                    "success": False,
                    "data": None,
                    "error": "Failed to create video"
                }), 500
            
            # Make the path relative to static folder for client access
            video_path = '/' + os.path.relpath(final_video, 'static').replace('\\', '/')
            
            # Save to database
            db.cursor.execute(
                """
                INSERT INTO videos (script_id, video_path, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (script_id, final_video)
            )
            db.conn.commit()
            video_id = db.cursor.lastrowid
            
            return jsonify({
                "success": True,
                "data": {
                    "video_id": video_id,
                    "video_path": video_path,
                    "title": title
                },
                "error": None
            })
        except Exception as e:
            print(f"Error in video creation: {e}")
            traceback.print_exc()
            raise
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "data": None,
            "error": str(e)
        }), 500

@app.route('/api/generate_video_from_custom_text', methods=['POST'])
def generate_video_from_custom_text():
    try:
        data = request.json
        title = data.get('title')
        text_content = data.get('text')
        
        if not title or not text_content:
            return jsonify({
                "success": False,
                "data": None,
                "error": "Title and text content are required"
            }), 400
        
        # Use your existing method to create a video from text
        result = video_creator.create_video_from_text(title, text_content)
        
        # Handle the various possible return types from create_video_from_text
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
        
        # Make paths relative to static folder for client access
        video_url = '/' + os.path.relpath(video_path, 'static').replace('\\', '/')
        vertical_url = ('/' + os.path.relpath(vertical_path, 'static').replace('\\', '/')) if vertical_path else None
        
        # Get keywords for reference
        keywords = keyword_extractor.extract_keywords(title, text_content)
        
        # Save to database if needed
        from datetime import datetime
        video_id = int(datetime.now().strftime("%Y%m%d%H%M%S"))
        
        video_path_str = video_path
        if vertical_path:
            video_path_str = f"{video_path}|{vertical_path}"
            
        db.cursor.execute(
            """
            INSERT INTO videos 
            (id, title, script_text, video_path, keywords, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                video_id,
                title,
                text_content,
                video_path_str,
                ",".join(keywords),
                datetime.now().isoformat()
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

def update_progress_file(message):
    """Update a progress file that could be polled by a client"""
    progress_path = os.path.join(app.static_folder, 'progress.json')
    try:
        with open(progress_path, 'w') as f:
            json.dump({
                'timestamp': datetime.datetime.now().isoformat(),
                'message': message
            }, f)
    except Exception as e:
        print(f"Failed to write progress: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)  # Disable reloader to prevent interruptions