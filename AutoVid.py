import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
import sqlite3
import openai
from dotenv import load_dotenv
import re
import tempfile
import shutil
import subprocess

# Try to import moviepy, but continue if it fails
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    print("Warning: MoviePy not available. Video creation functionality will be disabled.")
    MOVIEPY_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

class GNewsAPI:
    def __init__(self, api_key=None):
        # Use the provided API key or try to get from environment
        self.api_key = api_key or os.environ.get("GNEWS_API_KEY")
        if not self.api_key:
            raise ValueError("GNews API key is required")
        self.base_url = "https://gnews.io/api/v4"
    
    def get_top_headlines(self, country="us", language="en", max_results=5):
        """
        Get top headlines from the United States (or another country).
        
        Parameters:
        - country: Two-letter ISO 3166-1 country code (default: 'us' for United States)
        - language: Two-letter ISO 639-1 language code (default: 'en' for English)
        - max_results: Number of results to return (default: 5)
        """
        url = f"{self.base_url}/top-headlines"
        
        params = {
            "country": country,
            "lang": language,
            "max": max_results,
            "apikey": self.api_key
        }
        
        try:
            print(f"Making request to {url} with API key: {self.api_key[:5]}...")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error response: {response.status_code}")
                print(f"Response content: {response.text}")
                raise Exception(f"Request failed with status {response.status_code}: {response.text}")
            
            news_data = response.json()
            
            # Extract article titles and information
            articles_list = []
            for article in news_data.get("articles", []):
                articles_list.append({
                    "title": article.get("title", "No title"),
                    "source": article.get("source", {}).get("name", "Unknown source"),
                    "published_at": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                    "description": article.get("description", "")
                })
            
            # Convert to DataFrame
            df = pd.DataFrame(articles_list)
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            raise
    
    def search_news(self, query, language="en", country="us", max_results=5):
        """
        Search for news articles with a specific query.
        
        Parameters:
        - query: Keywords or phrases to search for
        - language: Two-letter ISO 639-1 language code (default: 'en' for English)
        - country: Two-letter ISO 3166-1 country code (default: 'us' for United States)
        - max_results: Number of results to return (default: 5)
        """
        url = f"{self.base_url}/search"
        
        params = {
            "q": query,
            "lang": language,
            "country": country,
            "max": max_results,
            "apikey": self.api_key
        }
        
        try:
            print(f"Making request to {url} with query: '{query}'...")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error response: {response.status_code}")
                print(f"Response content: {response.text}")
                raise Exception(f"Request failed with status {response.status_code}: {response.text}")
            
            news_data = response.json()
            
            # Extract article titles and information
            articles_list = []
            for article in news_data.get("articles", []):
                articles_list.append({
                    "title": article.get("title", "No title"),
                    "source": article.get("source", {}).get("name", "Unknown source"),
                    "published_at": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                    "description": article.get("description", "")
                })
            
            # Convert to DataFrame
            df = pd.DataFrame(articles_list)
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            raise

# Alternative news source using RSS feeds
class RSSNewsScraper:
    def __init__(self):
        self.rss_feeds = {
            "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "Washington Post": "http://feeds.washingtonpost.com/rss/national",
            "USA Today": "http://rssfeeds.usatoday.com/usatoday-NewsTopStories",
            "NPR": "https://feeds.npr.org/1001/rss.xml"
        }
    
    def get_top_headlines(self, limit=5):
        """
        Get top headlines from Romanian RSS feeds
        """
        try:
            import feedparser
            
            all_articles = []
            
            for source, url in self.rss_feeds.items():
                try:
                    print(f"Fetching RSS feed from {source}...")
                    feed = feedparser.parse(url)
                    
                    for entry in feed.entries[:limit]:
                        all_articles.append({
                            "title": entry.get("title", "No title"),
                            "source": source,
                            "published_at": entry.get("published", ""),
                            "url": entry.get("link", ""),
                            "description": entry.get("summary", "")
                        })
                except Exception as e:
                    print(f"Error fetching RSS feed from {source}: {e}")
            
            # Convert to DataFrame and sort by published date
            df = pd.DataFrame(all_articles)
            if not df.empty and 'published_at' in df.columns:
                df = df.sort_values(by="published_at", ascending=False)
            return df
            
        except ImportError:
            print("feedparser module not found. Please install it with: pip install feedparser")
            return pd.DataFrame()

class NewsDatabase:
    def __init__(self, db_path="news_database.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create news articles table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                source TEXT,
                url TEXT,
                published_at TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_for_script BOOLEAN DEFAULT 0
            )
            ''')
            
            # Create scripts table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER,
                script_text TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news_articles (id)
            )
            ''')
            
            # Create videos table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER,
                video_path TEXT NOT NULL,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (script_id) REFERENCES scripts (id)
            )
            ''')
            
            self.conn.commit()
            print("Database initialized successfully")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def add_news_articles(self, articles_df):
        """Add news articles to the database"""
        if articles_df.empty:
            print("No articles to add to database")
            return []
        
        added_ids = []
        
        try:
            for _, article in articles_df.iterrows():
                # Check if article already exists (by URL or title)
                self.cursor.execute(
                    "SELECT id FROM news_articles WHERE url = ? OR title = ?", 
                    (article.get('url', ''), article.get('title', ''))
                )
                existing = self.cursor.fetchone()
                
                if existing:
                    print(f"Article already exists in database: {article.get('title', 'No title')}")
                    added_ids.append(existing[0])
                    continue
                
                # Insert new article
                self.cursor.execute(
                    "INSERT INTO news_articles (title, description, source, url, published_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        article.get('title', 'No title'),
                        article.get('description', ''),
                        article.get('source', 'Unknown'),
                        article.get('url', ''),
                        article.get('published_at', '')
                    )
                )
                
                article_id = self.cursor.lastrowid
                added_ids.append(article_id)
                print(f"Added article to database: {article.get('title', 'No title')}")
            
            self.conn.commit()
            return added_ids
            
        except sqlite3.Error as e:
            print(f"Error adding articles to database: {e}")
            self.conn.rollback()
            return []
    
    def get_unused_articles(self, limit=5):
        """Get articles that haven't been used for script generation yet"""
        try:
            self.cursor.execute(
                "SELECT id, title, description, source FROM news_articles WHERE used_for_script = 0 ORDER BY fetched_at DESC LIMIT ?",
                (limit,)
            )
            articles = self.cursor.fetchall()
            return articles
        except sqlite3.Error as e:
            print(f"Error fetching unused articles: {e}")
            return []
    
    def mark_article_as_used(self, article_id):
        """Mark an article as used for script generation"""
        try:
            self.cursor.execute(
                "UPDATE news_articles SET used_for_script = 1 WHERE id = ?",
                (article_id,)
            )
            self.conn.commit()
            print(f"Marked article {article_id} as used")
        except sqlite3.Error as e:
            print(f"Error marking article as used: {e}")
            self.conn.rollback()
    
    def add_script(self, article_id, script_text):
        """Add a generated script to the database"""
        try:
            self.cursor.execute(
                "INSERT INTO scripts (news_id, script_text) VALUES (?, ?)",
                (article_id, script_text)
            )
            self.conn.commit()
            script_id = self.cursor.lastrowid
            print(f"Added script for article {article_id} with script ID {script_id}")
            return script_id
        except sqlite3.Error as e:
            print(f"Error adding script to database: {e}")
            self.conn.rollback()
            return None
    
    def get_recent_scripts(self, limit=5):
        """Get recently generated scripts with their associated article titles"""
        try:
            self.cursor.execute(
                """
                SELECT s.id, n.title, s.script_text, s.generated_at 
                FROM scripts s
                JOIN news_articles n ON s.news_id = n.id
                ORDER BY s.generated_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            scripts = self.cursor.fetchall()
            return scripts
        except sqlite3.Error as e:
            print(f"Error fetching recent scripts: {e}")
            return []
    
    def add_video(self, script_id, video_path, keywords):
        """Add a generated video to the database"""
        try:
            keywords_str = ','.join(keywords) if isinstance(keywords, list) else keywords
            
            self.cursor.execute(
                "INSERT INTO videos (script_id, video_path, keywords) VALUES (?, ?, ?)",
                (script_id, video_path, keywords_str)
            )
            self.conn.commit()
            video_id = self.cursor.lastrowid
            print(f"Added video for script {script_id} with video ID {video_id}")
            return video_id
        except sqlite3.Error as e:
            print(f"Error adding video to database: {e}")
            self.conn.rollback()
            return None
    
    def get_scripts_without_videos(self, limit=5):
        """Get scripts that don't have associated videos yet"""
        try:
            self.cursor.execute(
                """
                SELECT s.id, s.news_id, n.title, s.script_text 
                FROM scripts s
                JOIN news_articles n ON s.news_id = n.id
                LEFT JOIN videos v ON s.id = v.script_id
                WHERE v.id IS NULL
                ORDER BY s.generated_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            scripts = self.cursor.fetchall()
            return scripts
        except sqlite3.Error as e:
            print(f"Error fetching scripts without videos: {e}")
            return []
    
    def get_recent_videos(self, limit=5):
        """Get recently created videos with their associated article titles and scripts"""
        try:
            self.cursor.execute(
                """
                SELECT v.id, n.title, s.script_text, v.video_path, v.keywords, v.created_at 
                FROM videos v
                JOIN scripts s ON v.script_id = s.id
                JOIN news_articles n ON s.news_id = n.id
                ORDER BY v.created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            videos = self.cursor.fetchall()
            return videos
        except sqlite3.Error as e:
            print(f"Error fetching recent videos: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")

class ScriptGenerator:
    def __init__(self, api_key=None):
        # Get API key from environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required for script generation")
        
        openai.api_key = self.api_key
    
    def generate_script(self, title, description, duration_seconds=60):
        """Generate a short video script based on news title and description"""
        try:
            prompt = f"""
            Create a short, factual news script for a 30-60 second video about the following topic:
            
            Title: {title}
            
            Description: {description}
            
            The script should:
            1. Be approximately {duration_seconds} seconds when read aloud
            2. Focus ONLY on the news content - no greetings, introductions, or sign-offs
            3. Cover the key points from the description in a clear, direct manner
            4. Use a professional news tone suitable for broadcast
            5. Be in English language
            6. Start and end with the news content itself - no "hello", "welcome", "goodbye" or similar phrases
            
            Format the script as plain text that could be read by a news presenter.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional news writer who creates concise, direct news scripts without any greetings or sign-offs."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            script = response.choices[0].message.content.strip()
            return script
            
        except Exception as e:
            print(f"Error generating script: {e}")
            return f"Failed to generate script for '{title}'. Error: {str(e)}"

class KeywordExtractor:
    def __init__(self, api_key=None):
        # Get API key from environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required for keyword extraction")
        
        openai.api_key = self.api_key
    
    def extract_keywords(self, title, description, max_keywords=5):
        """Extract relevant keywords from news title and description"""
        try:
            prompt = f"""
            Extract {max_keywords} keywords from this news article that would be useful for finding relevant stock videos.
            
            Include a mix of:
            1. Specific keywords directly related to the article topic
            2. Generic visual concepts that represent the article's theme (like "business meeting" for corporate news)
            3. Emotional or atmospheric terms that capture the mood (like "celebration" or "tension")
            
            Title: {title}
            
            Description: {description}
            
            Return ONLY the keywords separated by commas, with no additional text.
            Make sure the keywords are good for video search on stock footage sites.
            
            Example output format: keyword1, keyword2, keyword3, keyword4, keyword5
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a keyword extraction tool that generates effective search termsjj for finding stock videos related to news articles. You provide a mix of specific and generic visual concepts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            keywords = response.choices[0].message.content.strip()
            # Split by comma and strip whitespace
            keyword_list = [k.strip() for k in keywords.split(',')]
            
            # Add some generic fallback keywords if we don't have enough
            fallback_keywords = ["news", "information", "report", "media", "journalism", 
                                "broadcast", "current events", "documentary", "coverage"]
            
            # Ensure we have enough keywords by adding fallbacks if needed
            while len(keyword_list) < max_keywords and fallback_keywords:
                fallback = fallback_keywords.pop(0)
                if fallback not in keyword_list:
                    keyword_list.append(fallback)
            
            return keyword_list
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback: extract nouns from title and description
            words = re.findall(r'\b\w+\b', f"{title} {description}")
            # Filter out short words and common stop words
            stop_words = ['the', 'and', 'or', 'in', 'on', 'at', 'to', 'a', 'an', 'for', 'with', 'by', 'is', 'are', 'was', 'were']
            keywords = [w for w in words if len(w) > 3 and w.lower() not in stop_words]
            
            # Add some generic fallback keywords
            generic_keywords = ["news", "information", "report", "media"]
            keywords.extend(generic_keywords)
            
            # Return unique keywords up to max_keywords
            unique_keywords = list(dict.fromkeys(keywords))  # Remove duplicates while preserving order
            return unique_keywords[:max_keywords]
    
    def enhance_video_search(self, keywords, article_category=None):
        """
        Enhance keywords for better video search results
        
        Parameters:
        - keywords: List of initial keywords
        - article_category: Optional category of the article (politics, sports, etc.)
        
        Returns:
        - Enhanced list of keywords with visual terms added
        """
        # Define visual enhancers by category
        visual_enhancers = {
            "politics": ["podium", "flag", "government building", "press conference", "debate"],
            "business": ["office", "meeting", "handshake", "stock market", "corporate"],
            "technology": ["computer", "digital", "innovation", "laboratory", "device"],
            "sports": ["stadium", "athlete", "competition", "game", "training"],
            "health": ["hospital", "medical", "doctor", "patient", "healthcare"],
            "environment": ["nature", "landscape", "climate", "pollution", "conservation"],
            "general": ["city", "people", "crowd", "building", "street", "skyline"]
        }
        
        enhanced_keywords = keywords.copy()
        
        # If we know the category, add some visual enhancers from that category
        if article_category and article_category.lower() in visual_enhancers:
            category_enhancers = visual_enhancers[article_category.lower()]
            for enhancer in category_enhancers[:2]:  # Add up to 2 category-specific enhancers
                if enhancer not in enhanced_keywords:
                    enhanced_keywords.append(enhancer)
        
        # Always add some general visual enhancers
        for enhancer in visual_enhancers["general"]:
            if enhancer not in enhanced_keywords and len(enhanced_keywords) < 8:
                enhanced_keywords.append(enhancer)
        
        return enhanced_keywords[:8]  # Limit to 8 keywords

class PexelsAPI:
    def __init__(self, api_key=None):
        # Use the provided API key or try to get from environment
        self.api_key = api_key or os.environ.get("PEXELS_API_KEY")
        if not self.api_key:
            raise ValueError("Pexels API key is required")
        self.base_url = "https://api.pexels.com/videos"
        self.headers = {
            "Authorization": self.api_key
        }
    
    def search_videos(self, query, per_page=5, orientation="landscape", min_duration=5, max_duration=20):
        """
        Search for videos on Pexels based on a query
        
        Parameters:
        - query: Search term
        - per_page: Number of results to return (default: 5)
        - orientation: Video orientation (landscape, portrait, square)
        - min_duration: Minimum video duration in seconds
        - max_duration: Maximum video duration in seconds
        """
        url = f"{self.base_url}/search"
        
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": "medium",  # Prefer medium-sized videos for better quality
        }
        
        try:
            print(f"Searching Pexels for videos with query: '{query}'...")
            response = requests.get(url, params=params, headers=self.headers)
            
            if response.status_code != 200:
                print(f"Error response: {response.status_code}")
                print(f"Response content: {response.text}")
                raise Exception(f"Request failed with status {response.status_code}: {response.text}")
            1
            videos_data = response.json()
            
            # Extract video information
            videos_list = []
            for video in videos_data.get("videos", []):
                # Get the HD or SD file URL
                video_files = video.get("video_files", [])
                video_url = None
                
                # Try to get HD quality first, then fall back to SD
                for file in video_files:
                    if file.get("quality") == "hd" and file.get("width") >= 1280:
                        video_url = file.get("link")
                        break
                
                # If no HD, get any file
                if not video_url and video_files:
                    video_url = video_files[0].get("link")
                
                # Check if the video duration is within our desired range
                duration = video.get("duration", 0)
                if video_url and min_duration <= duration <= max_duration:
                    videos_list.append({
                        "id": video.get("id"),
                        "url": video_url,
                        "duration": duration,
                        "width": video.get("width"),
                        "height": video.get("height"),
                        "user": video.get("user", {}).get("name"),
                        "preview": video.get("image"),
                        "query": query  # Store the query that found this video
                    })
            
            return videos_list
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return []

class VideoCreator:
    def __init__(self, output_dir="videos"):
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Find FFmpeg executable
        self.ffmpeg_path = self.find_ffmpeg()
        if self.ffmpeg_path:
            self.ffmpeg_available = True
            print(f"FFmpeg found at: {self.ffmpeg_path}")
        else:
            self.ffmpeg_available = False
            print("FFmpeg not found. Video creation will be limited to downloading only.")
        
        if not MOVIEPY_AVAILABLE:
            print("Warning: MoviePy not available. Will try to use FFmpeg directly for video creation.")
    
    def find_ffmpeg(self):
        """Find the FFmpeg executable path"""
        # Common locations for FFmpeg
        possible_paths = [
            "ffmpeg",                          # If in PATH
            "C:\\ffmpeg\\bin\\ffmpeg.exe",     # Common Windows install location
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe",  # Your specific path
            os.path.expanduser("~/ffmpeg/bin/ffmpeg"),
            os.path.expanduser("~/.local/bin/ffmpeg"),
            "/usr/bin/ffmpeg",                 # Linux/Mac locations
            "/usr/local/bin/ffmpeg",
        ]
        
        # Try to find ffmpeg in the possible locations
        for path in possible_paths:
            try:
                print(f"Checking for FFmpeg at: {path}")
                result = subprocess.run([path, "-version"], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE, 
                                       shell=True)
                if result.returncode == 0:
                    print(f"FFmpeg found at: {path}")
                    return path
            except Exception as e:
                print(f"Error checking {path}: {e}")
                continue
        
        # Ask the user for the FFmpeg path if not found
        print("FFmpeg not found in common locations.")
        user_path = input("Please enter the full path to ffmpeg executable (or press Enter to skip): ")
        if user_path and os.path.exists(user_path):
            return user_path
        
        return None
    
    def download_video(self, url, output_path):
        """Download a video from URL to the specified path"""
        try:
            print(f"Downloading video from {url}...")
            response = requests.get(url, stream=True)
            
            if response.status_code != 200:
                print(f"Error downloading video: {response.status_code}")
                return False
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Video downloaded to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            return False
    
    def create_simple_video(self, script, videos, output_filename=None):
        """
        Create a simple video from the first available clip with text overlay
        
        Parameters:
        - script: The script text to use for the video
        - videos: List of video information dictionaries from Pexels API
        - output_filename: Name for the output file (optional)
        """
        if not videos:
            print("No videos available to create the video")
            return None
        
        if not self.ffmpeg_available:
            print("FFmpeg not available. Cannot create video.")
            return None
        
        if not output_filename:
            # Generate a filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"news_video_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create a temporary directory for downloaded videos
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Download just the first video
            first_video = videos[0]
            video_path = os.path.join(temp_dir, "video.mp4")
            
            if not self.download_video(first_video["url"], video_path):
                print("Failed to download video")
                return None
            
            print(f"Successfully downloaded video to {video_path}")
            
            # Save the script to a text file alongside the video
            script_path = output_path.replace('.mp4', '_script.txt')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            print(f"Script saved to {script_path}")
            
            # Create a simple video - just trim the video
            simple_cmd = [
                self.ffmpeg_path,
                "-v", "warning",  # Only show warnings and errors
                "-i", video_path,
                "-t", "30",
                "-c:v", "copy",
                "-y",
                output_path
            ]
            
            print(f"Creating simple video...")
            
            try:
                # Run with minimal output
                subprocess.run(simple_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                print(f"✓ Successfully created simple video: {output_path}")
                return output_path
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to create video")
                if e.stderr:
                    error_text = e.stderr.decode()
                    # Only print the last few lines of the error
                    error_lines = error_text.strip().split('\n')
                    if len(error_lines) > 3:
                        print("Error details: " + '\n'.join(error_lines[-3:]))
                    else:
                        print("Error details: " + error_text)
                return None
        
        except Exception as e:
            print(f"Error creating simple video: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary files in {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")

    def create_video(self, script, videos, output_filename=None):
        """
        Create a video by combining clips with the script
        
        Parameters:
        - script: The script text to use for the video
        - videos: List of video information dictionaries from Pexels API
        - output_filename: Name for the output file (optional)
        """
        if not videos:
            print("No videos available to create the video")
            return None
        
        if not output_filename:
            # Generate a filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"news_video_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create a temporary directory for downloaded videos
        temp_dir = tempfile.mkdtemp()
        downloaded_videos = []
        
        try:
            # Download videos (up to 5 for a 30-second video with 6 seconds per clip)
            max_videos = min(5, len(videos))
            print(f"Downloading {max_videos} videos for a {max_videos * 6} second video...")
            
            for i in range(max_videos):
                video_path = os.path.join(temp_dir, f"video_{i}.mp4")
                if self.download_video(videos[i]["url"], video_path):
                    downloaded_videos.append(video_path)
            
            if not downloaded_videos:
                print("Failed to download any videos")
                return None
            
            print(f"Successfully downloaded {len(downloaded_videos)} videos")
            
            # Save the script to a text file alongside the video
            script_path = output_path.replace('.mp4', '_script.txt')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            print(f"Script saved to {script_path}")
            
            # Try to concatenate videos
            if len(downloaded_videos) > 1:
                print(f"Attempting to concatenate {len(downloaded_videos)} videos (6 seconds each)...")
                concatenated_video = self.concatenate_videos(downloaded_videos, output_path, script)
                
                if concatenated_video:
                    print(f"Successfully created concatenated video: {concatenated_video}")
                    return concatenated_video
            
            # If concatenation fails or only one video, try the simple approach
            if len(downloaded_videos) == 1 or not concatenated_video:
                print("Attempting to create a simple video from the first clip...")
                simple_video = self.create_simple_video(script, videos, output_filename)
                
                if simple_video:
                    print(f"Successfully created simple video: {simple_video}")
                    return simple_video
            
            # If both approaches fail, fall back to downloading individual videos
            print("Video creation failed. Saving individual videos instead...")
            
            # Create a directory for the downloaded videos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_dir = os.path.join(self.output_dir, f"downloads_{timestamp}")
            os.makedirs(download_dir, exist_ok=True)
            
            # Copy downloaded videos to the download directory
            for i, video_path in enumerate(downloaded_videos):
                dest_path = os.path.join(download_dir, f"video_{i}.mp4")
                shutil.copy2(video_path, dest_path)
            
            # Save the script to a text file
            script_path = os.path.join(download_dir, "script.txt")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            print(f"Downloaded {len(downloaded_videos)} videos to {download_dir}")
            print(f"Script saved to {script_path}")
            
            return download_dir
            
        except Exception as e:
            print(f"Error creating video: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Clean up temporary directory and downloaded videos
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary files in {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")

    def concatenate_videos(self, video_paths, output_path, script_text=None):
        """
        Concatenate multiple videos into one continuous video
        
        Parameters:
        - video_paths: List of paths to video files
        - output_path: Path for the output concatenated video
        - script_text: Optional script text to add as overlay
        
        Returns:
        - Path to the concatenated video if successful, None otherwise
        """
        if not video_paths:
            print("No videos to concatenate.")
            return None
        
        if not self.ffmpeg_available:
            print("FFmpeg not available. Cannot concatenate videos.")
            return None
        
        try:
            # Limit to 5 videos maximum (30 seconds total with 6 seconds each)
            video_paths = video_paths[:5]
            print(f"Concatenating {len(video_paths)} videos (6 seconds each)...")
            
            # Create a temporary directory for processed videos
            temp_dir = tempfile.mkdtemp()
            processed_videos = []
            
            # First, process each video to ensure compatibility
            for i, video_path in enumerate(video_paths):
                # Limit each video to 6 seconds and ensure consistent format
                processed_path = os.path.join(temp_dir, f"proc_{i}.mp4")
                process_cmd = [
                    self.ffmpeg_path,
                    "-v", "warning",  # Only show warnings and errors
                    "-i", video_path,
                    "-t", "6",  # Limit to 6 seconds
                    "-vf", "scale=1280:720",  # Standardize resolution
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "22",
                    "-y",
                    processed_path
                ]
                
                print(f"Processing video {i+1}/{len(video_paths)}...")
                
                # Run the command with minimal output
                try:
                    result = subprocess.run(
                        process_cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        shell=True,
                        check=True
                    )
                    processed_videos.append(processed_path)
                    print(f"✓ Successfully processed video {i+1}")
                except subprocess.CalledProcessError as e:
                    print(f"✗ Error processing video {i+1}")
                    if e.stderr:
                        error_text = e.stderr.decode()
                        # Only print the last few lines of the error
                        error_lines = error_text.strip().split('\n')
                        if len(error_lines) > 3:
                            print("Error details: " + '\n'.join(error_lines[-3:]))
                        else:
                            print("Error details: " + error_text)
            
            if not processed_videos:
                print("No videos to concatenate after processing.")
                return None
            
            # Create a file list for concatenation
            list_file = os.path.join(temp_dir, "file_list.txt")
            with open(list_file, 'w') as f:
                for video in processed_videos:
                    f.write(f"file '{os.path.abspath(video)}'\n")
            
            # Run the concatenation command
            concat_cmd = [
                self.ffmpeg_path,
                "-v", "warning",  # Only show warnings and errors
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                output_path
            ]
            
            print(f"Running concatenation command...")
            
            try:
                # Run with minimal output
                subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                
                # Calculate the expected duration (6 seconds per video)
                expected_duration = len(processed_videos) * 6
                print(f"✓ Successfully created concatenated video: {output_path} (Expected duration: ~{expected_duration} seconds)")
                
                return output_path
            except subprocess.CalledProcessError as e:
                print(f"✗ Error creating concatenated video")
                if e.stderr:
                    error_text = e.stderr.decode()
                    # Only print the last few lines of the error
                    error_lines = error_text.strip().split('\n')
                    if len(error_lines) > 3:
                        print("Error details: " + '\n'.join(error_lines[-3:]))
                    else:
                        print("Error details: " + error_text)
                return None
        
        except Exception as e:
            print(f"Error in concatenate_videos: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")

# Simple test script
if __name__ == "__main__":
    print("Initializing News System...")
    
    # Initialize database
    db = NewsDatabase()
    
    # Get news articles
    top_titles = []
    articles_df = pd.DataFrame()
    
    # First try with GNews API
    try:
        print("\n--- TRYING GNEWS API ---")
        news_api = GNewsAPI()
        
        # First try searching for US news
        print("Searching for US news...")
        try:
            us_news = news_api.search_news(query="United States", max_results=5)
            if not us_news.empty:
                print("\nTop news about the United States:")
                for i, (_, article) in enumerate(us_news.iterrows(), 1):
                    print(f"{i}. {article['title']} ({article['source']})")
                    print(f"   {article['description'][:100]}...")
                    print(f"   URL: {article['url']}")
                    print()
                
                articles_df = us_news
                top_titles = us_news["title"].tolist()
            else:
                raise Exception("No results found for US search")
                
        except Exception as e:
            print(f"Error searching for US news: {e}")
            
            # Try top headlines instead
            print("\nFetching top headlines...")
            headlines = news_api.get_top_headlines(country="us", max_results=5)
            
            if not headlines.empty:
                print("\nTop 5 news headlines in the United States:")
                for i, (_, article) in enumerate(headlines.iterrows(), 1):
                    print(f"{i}. {article['title']} ({article['source']})")
                    print(f"   {article['description'][:100]}...")
                    print(f"   URL: {article['url']}")
                    print()
                
                articles_df = headlines
                top_titles = headlines["title"].tolist()
            else:
                print("No headlines found.")
            
    except Exception as e:
        print(f"Error with GNews API: {e}")
        print("Falling back to RSS feeds...")
        
        try:
            print("\n--- TRYING RSS FEEDS ---")
            rss_scraper = RSSNewsScraper()
            
            print("Fetching top headlines from Romanian RSS feeds...")
            rss_headlines = rss_scraper.get_top_headlines(limit=10)
            
            if not rss_headlines.empty:
                print("\nTop news headlines from Romanian sources:")
                for i, (_, article) in enumerate(rss_headlines.head(10).iterrows(), 1):
                    print(f"{i}. {article['title']} ({article['source']})")
                    if 'description' in article and article['description']:
                        print(f"   {article['description'][:100]}...")
                    print(f"   URL: {article['url']}")
                    print()
                
                articles_df = rss_headlines.head(5)
                top_titles = rss_headlines["title"].tolist()[:5]
            else:
                print("No headlines found from RSS feeds.")
                
        except Exception as e:
            print(f"Error with RSS feeds: {e}")
            print("Falling back to predefined US news topics...")
            us_topics = [
                "US Politics", 
                "US Economy", 
                "US Sports", 
                "US Health", 
                "US Technology"
            ]
            
            print("\nPredefined US news topics:")
            for i, topic in enumerate(us_topics, 1):
                print(f"{i}. {topic}")
            
            top_titles = us_topics

    # Print the final list of top titles
    print("\nFinal list of top titles:")
    for i, title in enumerate(top_titles[:5], 1):
        print(f"{i}. {title}")
    
    # Add articles to database
    if not articles_df.empty:
        print("\nAdding articles to database...")
        added_ids = db.add_news_articles(articles_df)
        print(f"Added {len(added_ids)} articles to database")
    
    # Interactive menu for script generation and video creation
    try:
        # Use environment variable for API key
        script_generator = ScriptGenerator()
        keyword_extractor = KeywordExtractor()
        pexels_api = PexelsAPI()
        video_creator = VideoCreator()
        
        while True:
            print("\n--- MAIN MENU ---")
            print("1. Generate script for a new article")
            if MOVIEPY_AVAILABLE:
                print("2. Create video for an article")
            else:
                print("2. Download videos for an article (MoviePy not available)")
            print("3. View recent scripts")
            print("4. View recent videos")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == "1":
                # Get unused articles
                unused_articles = db.get_unused_articles()
                
                if not unused_articles:
                    print("No unused articles available. Please fetch more news.")
                    continue
                
                print("\nAvailable articles:")
                for i, (article_id, title, _, source) in enumerate(unused_articles, 1):
                    print(f"{i}. [{article_id}] {title} ({source})")
                
                article_choice = input("\nEnter the number of the article to use (or 0 to cancel): ")
                if article_choice == "0":
                    continue
                
                try:
                    article_index = int(article_choice) - 1
                    if 0 <= article_index < len(unused_articles):
                        article_id, title, description, _ = unused_articles[article_index]
                        
                        print(f"\nGenerating script for: {title}")
                        script = script_generator.generate_script(title, description)
                        
                        print("\nGenerated Script:")
                        print("-" * 50)
                        print(script)
                        print("-" * 50)
                        
                        save_choice = input("\nSave this script to database? (y/n): ")
                        if save_choice.lower() == "y":
                            script_id = db.add_script(article_id, script)
                            if script_id:
                                db.mark_article_as_used(article_id)
                                print(f"Script saved with ID: {script_id}")
                    else:
                        print("Invalid article number.")
                except ValueError:
                    print("Please enter a valid number.")
            
            elif choice == "2":
                # Get scripts without videos
                scripts_without_videos = db.get_scripts_without_videos()
                
                if not scripts_without_videos:
                    print("No scripts available for video creation. Please generate scripts first.")
                    continue
                
                print("\nAvailable scripts for video creation:")
                for i, (script_id, news_id, title, _) in enumerate(scripts_without_videos, 1):
                    print(f"{i}. [{script_id}] {title}")
                
                script_choice = input("\nEnter the number of the script to use (or 0 to cancel): ")
                if script_choice == "0":
                    continue
                
                try:
                    script_index = int(script_choice) - 1
                    if 0 <= script_index < len(scripts_without_videos):
                        script_id, news_id, title, script_text = scripts_without_videos[script_index]
                        
                        # Get the full article details for keyword extraction
                        db.cursor.execute(
                            "SELECT title, description FROM news_articles WHERE id = ?",
                            (news_id,)
                        )
                        article = db.cursor.fetchone()
                        
                        if not article:
                            print("Article not found in database.")
                            continue
                        
                        article_title, article_description = article
                        
                        print(f"\nExtracting keywords for: {article_title}")
                        keywords = keyword_extractor.extract_keywords(article_title, article_description)
                        print(f"Initial keywords: {', '.join(keywords)}")

                        # Try to determine the article category
                        article_category = "general"
                        category_keywords = ["politics", "business", "technology", "sports", "health", "environment"]
                        for category in category_keywords:
                            if category.lower() in article_title.lower() or category.lower() in article_description.lower():
                                article_category = category
                                break

                        # Enhance keywords for better video search
                        enhanced_keywords = keyword_extractor.enhance_video_search(keywords, article_category)
                        print(f"Enhanced keywords for video search: {', '.join(enhanced_keywords)}")

                        # Search for videos for each keyword
                        all_videos = []
                        for keyword in enhanced_keywords:
                            videos = pexels_api.search_videos(keyword, per_page=2)
                            if videos:
                                print(f"Found {len(videos)} videos for keyword '{keyword}'")
                                all_videos.extend(videos)
                                if len(all_videos) >= 5:
                                    break
                            else:
                                print(f"No videos found for keyword '{keyword}'")

                        if not all_videos:
                            print("No videos found for any of the extracted keywords.")
                            # Try with more generic keywords as a fallback
                            generic_keywords = ["news", "information", "media", "people", "city", "business"]
                            for keyword in generic_keywords:
                                videos = pexels_api.search_videos(keyword, per_page=2)
                                if videos:
                                    print(f"Found {len(videos)} videos for generic keyword '{keyword}'")
                                    all_videos.extend(videos)
                                    if len(all_videos) >= 5:
                                        break
                            
                            if not all_videos:
                                print("Could not find any videos, even with generic keywords.")
                                continue

                        print(f"\nFound a total of {len(all_videos)} videos for the keywords.")

                        # Create the video
                        print("\nCreating video...")
                        video_path = video_creator.create_video(script_text, all_videos)

                        if video_path:
                            # Add video to database
                            video_id = db.add_video(script_id, video_path, enhanced_keywords)
                            if video_id:
                                print(f"Video created and saved with ID: {video_id}")
                        else:
                            print("Failed to create video.")
                    else:
                        print("Invalid script number.")
                except ValueError:
                    print("Please enter a valid number.")
            
            elif choice == "3":
                recent_scripts = db.get_recent_scripts()
                
                if not recent_scripts:
                    print("No scripts found in the database.")
                    continue
                
                print("\nRecent Scripts:")
                for script_id, title, script_text, generated_at in recent_scripts:
                    print(f"\nScript ID: {script_id}")
                    print(f"Article: {title}")
                    print(f"Generated: {generated_at}")
                    print("-" * 50)
                    print(script_text[:200] + "..." if len(script_text) > 200 else script_text)
                    print("-" * 50)
                
                script_choice = input("\nEnter a script ID to view full text (or 0 to return): ")
                if script_choice == "0":
                    continue
                
                try:
                    script_id = int(script_choice)
                    for s_id, title, script_text, generated_at in recent_scripts:
                        if s_id == script_id:
                            print(f"\nFull Script for '{title}':")
                            print("-" * 50)
                            print(script_text)
                            print("-" * 50)
                            break
                    else:
                        print("Script ID not found.")
                except ValueError:
                    print("Please enter a valid number.")
            
            elif choice == "4":
                recent_videos = db.get_recent_videos()
                
                if not recent_videos:
                    print("No videos found in the database.")
                    continue
                
                print("\nRecent Videos:")
                for video_id, title, script_text, video_path, keywords, created_at in recent_videos:
                    print(f"\nVideo ID: {video_id}")
                    print(f"Article: {title}")
                    print(f"Created: {created_at}")
                    print(f"Keywords: {keywords}")
                    print(f"Video path: {video_path}")
                    print("-" * 50)
                
                video_choice = input("\nEnter a video ID to view details (or 0 to return): ")
                if video_choice == "0":
                    continue
                
                try:
                    video_id = int(video_choice)
                    for v_id, title, script_text, video_path, keywords, created_at in recent_videos:
                        if v_id == video_id:
                            print(f"\nFull Details for Video '{title}':")
                            print("-" * 50)
                            print(f"Script: {script_text}")
                            print(f"Keywords: {keywords}")
                            print(f"Video path: {video_path}")
                            print("-" * 50)
                            break
                    else:
                        print("Video ID not found.")
                except ValueError:
                    print("Please enter a valid number.")
            
            elif choice == "5":
                print("Exiting program.")
                break
            
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
    
    except Exception as e:
        print(f"Error in main menu: {e}")
    
    # Close database connection
    db.close()
    print("Program completed.")