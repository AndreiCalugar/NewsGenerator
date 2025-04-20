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
import math
import random

# Try to import moviepy, but continue if it fails
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    print("Warning: MoviePy not available. Video creation functionality will be disabled.")
    MOVIEPY_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# Add these imports at the top of your file
try:
    import pyttsx3  # For offline TTS
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("pyttsx3 not available. Will try other TTS options.")

try:
    from gtts import gTTS  # Google Text-to-Speech
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("gTTS not available. Will try other TTS options.")

class GNewsAPI:
    def __init__(self, api_key=None):
        # Use the provided API key or try to get from environment
        self.api_key = api_key or os.environ.get("GNEWS_API_KEY")
        if not self.api_key:
            raise ValueError("GNews API key is required")
        self.base_url = "https://gnews.io/api/v4"
    
    def get_top_headlines(self, country="us", language="en", max_results=8):
        """
        Get top headlines from the United States (or another country).
        
        Parameters:
        - country: Two-letter ISO 3166-1 country code (default: 'us' for United States)
        - language: Two-letter ISO 639-1 language code (default: 'en' for English)
        - max_results: Number of results to return (default: 8)
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
    
    def search_news(self, query, language="en", country="us", max_results=8):
        """
        Search for news articles by keyword
        
        Parameters:
        - query: Search term
        - language: Two-letter ISO 639-1 language code (default: 'en' for English)
        - country: Two-letter ISO 3166-1 country code (default: 'us' for United States)
        - max_results: Number of results to return (default: 8)
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
    
    def generate_script(self, article_title, article_text=None, max_words=90):
        """
        Generate a script for a news video
        
        Parameters:
        - article_title: Title of the news article
        - article_text: Text of the news article (optional)
        - max_words: Maximum number of words for the script (90 words ≈ 45 seconds of speech)
        
        Returns:
        - Generated script text
        """
        try:
            # Prepare the prompt
            if article_text:
                prompt = f"""Write a concise, factual news script for a 30-45 second video about this article:
Title: {article_title}
Content: {article_text}

The script MUST:
1. Be strictly factual and focused on the news content.
2. Be no more than {max_words} words (target: 30-45 seconds read aloud).
3. Start DIRECTLY with the news hook or main point. NO greetings like "Hey there" or "Welcome".
4. Include only the most important facts from the content.
5. End DIRECTLY after the last piece of news information. NO sign-offs like "Stay informed" or "Thanks for watching".
6. Use a professional, direct news reporting tone.

Format: Plain text script only.
"""
            else:
                prompt = f"""Write a concise, factual news script for a 30-45 second video based ONLY on this headline:
Headline: {article_title}

The script MUST:
1. Be strictly factual, speculating reasonably based *only* on the headline.
2. Be no more than {max_words} words (target: 30-45 seconds read aloud).
3. Start DIRECTLY with the news hook or main point derived from the headline. NO greetings like "Hey there" or "Welcome".
4. Focus on the likely core subject of the headline.
5. End DIRECTLY after the last piece of news information or brief summary. NO sign-offs like "Stay informed" or "Thanks for watching".
6. Use a professional, direct news reporting tone.

Format: Plain text script only.
"""

            # Get the API key from environment variable (this check might be redundant if already done in __init__)
            # api_key = os.environ.get("OPENAI_API_KEY")
            # if not api_key:
            #     raise ValueError("OpenAI API key not found in environment variables")
            # openai.api_key = api_key # Already set in __init__

            # Make the API call
            print("Generating script with OpenAI API...")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    # Updated system message for more directness
                    {"role": "system", "content": "You are a news script writer creating concise, factual scripts for short videos. You avoid all conversational filler, greetings, and sign-offs, focusing solely on delivering the news information directly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250, # Reduced slightly as filler is removed
                temperature=0.6 # Slightly lower temperature for more factual tone
            )
            
            # Extract the script from the response
            script = response.choices[0].message.content.strip()
            
            # Count words to verify length
            word_count = len(script.split())
            print(f"Generated script with {word_count} words (target: {max_words})")
            
            # If the script is too long, truncate it
            if word_count > max_words:
                print(f"Script is too long ({word_count} words). Truncating to approximately {max_words} words...")
                
                # Try to truncate at a sentence boundary
                sentences = re.split(r'(?<=[.!?])\s+', script)
                truncated_script = ""
                current_word_count = 0
                
                for sentence in sentences:
                    sentence_word_count = len(sentence.split())
                    if current_word_count + sentence_word_count <= max_words:
                        truncated_script += sentence + " "
                        current_word_count += sentence_word_count
                    else:
                        # Maybe add just the first few words of the next sentence if close?
                        # Or just break here for simplicity.
                        break 
                
                script = truncated_script.strip()
                # Ensure no trailing punctuation issues after truncation
                if script.endswith(('.', '!', '?')): 
                    pass # Looks okay
                else:
                    # Find last punctuation if any
                    last_punc = -1
                    for char in reversed(script):
                        if char in '.!?':
                            last_punc = script.rfind(char)
                            break
                    if last_punc != -1:
                        script = script[:last_punc+1] # Truncate to last full sentence end

                print(f"Truncated script to {len(script.split())} words")
            
            return script
            
        except Exception as e:
            print(f"Error generating script: {e}")
            import traceback
            traceback.print_exc()
            return None

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

    def search_videos(self, query, per_page=5, orientation="landscape"):
        """
        Search for videos on Pexels
        
        Parameters:
        - query: Search term
        - per_page: Number of results per page (default: 5, max: 80)
        - orientation: landscape, portrait, or square
        
        Returns:
        - List of video information dictionaries
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
            response = requests.get(url, params=params, headers={"Authorization": self.api_key})
            
            if response.status_code != 200:
                print(f"Error response: {response.status_code}")
                print(f"Response content: {response.text}")
                raise Exception(f"Request failed with status {response.status_code}: {response.text}")
            
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
                if video_url and 5 <= duration <= 20:
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

    def create_video_with_narration(self, script, video_sources, output_filename=None):
        """
        Create a video with narration, dividing narration time equally among video clips.
        
        Parameters:
        - script: The script text to use for the video
        - video_sources: List of dictionaries, each containing a video 'url' (expects ~5 sources)
        - output_filename: Name for the output file (optional)
        
        Returns:
        - Path to the created video if successful, None otherwise
        """
        if not video_sources:
            print("No video sources available to create the video")
            return None
        
        if not self.ffmpeg_available:
            print("FFmpeg not available. Cannot create video.")
            return None
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"news_video_{timestamp}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        narrated_output_path = output_path.replace('.mp4', '_narrated.mp4')
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 1. Generate Narration & Get Duration
            print("Generating narration from script...")
            audio_path = os.path.join(temp_dir, "narration.mp3")
            if not self.generate_speech(script, audio_path):
                print("Failed to generate speech. Cannot create narrated video.")
                return None
            
            narration_duration = self.get_audio_duration(audio_path)
            if not narration_duration:
                print("Could not determine narration duration. Using default 30s.")
                narration_duration = 30.0
            print(f"Narration duration: {narration_duration:.2f} seconds")

            # 2. Download Videos
            print(f"Downloading {len(video_sources)} videos...")
            downloaded_video_paths = []
            for i, video_info in enumerate(video_sources):
                video_path = os.path.join(temp_dir, f"download_{i}.mp4")
                if self.download_video(video_info["url"], video_path):
                    downloaded_video_paths.append(video_path)
            
            if not downloaded_video_paths:
                print("Failed to download any videos from the provided sources.")
                return None
            print(f"Successfully downloaded {len(downloaded_video_paths)} videos.")

            # Save the script
            script_path = output_path.replace('.mp4', '_script.txt')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            print(f"Script saved to {script_path}")

            # 3. Process Videos to Match Narration Segments
            processed_videos = []
            num_clips = len(downloaded_video_paths)
            clip_duration = narration_duration / num_clips if num_clips > 0 else narration_duration
            print(f"Each clip will be processed to fit {clip_duration:.2f} seconds.")
            
            for i, video_path in enumerate(downloaded_video_paths):
                processed_path = os.path.join(temp_dir, f"proc_{i}.mp4")
                
                # FFmpeg command to scale, set duration (padding if needed), remove audio
                process_cmd = [
                    self.ffmpeg_path,
                    "-i", video_path,
                    "-vf", f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,tpad=stop_mode=clone:stop_duration={clip_duration+1}", # Scale, pad, set fps, pad end
                    "-t", str(clip_duration), # Trim to exactly clip_duration
                    "-an",  # Remove original audio
                    "-c:v", "libx264", # Re-encode
                    "-preset", "fast",
                    "-crf", "23",
                    "-y",
                    processed_path
                ]
                
                print(f"Processing video {i+1}/{num_clips}...")
                try:
                    subprocess.run(process_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                    processed_videos.append(processed_path)
                    print(f"✓ Successfully processed video {i+1}")
                except subprocess.CalledProcessError as e:
                    print(f"✗ Error processing video {i+1}")
                    if e.stderr:
                        error_text = e.stderr.decode()
                        print(f"FFmpeg Error: {error_text}")
                    print("Skipping video due to error.")
            
            if not processed_videos:
                print("No videos were successfully processed.")
                return None

            # 4. Concatenate Processed Videos
            list_file = os.path.join(temp_dir, "file_list.txt")
            with open(list_file, 'w') as f:
                for video_path in processed_videos:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")
            
            silent_output = os.path.join(temp_dir, "silent_output.mp4")
            concat_cmd = [
                self.ffmpeg_path,
                "-v", "warning",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy", # Copy codec since segments are already encoded
                "-y",
                silent_output
            ]
            
            print("Concatenating videos...")
            try:
                subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                print("✓ Videos concatenated successfully")
            except subprocess.CalledProcessError as e:
                print("✗ Error concatenating videos")
                if e.stderr:
                    print("Error details: " + e.stderr.decode())
                return None

            # 5. Add Narration
            final_cmd = [
                self.ffmpeg_path,
                "-v", "warning",
                "-i", silent_output,
                "-i", audio_path,
                "-c:v", "copy", # Copy video stream
                "-c:a", "aac",  # Encode audio
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",  # Ensure final video length matches the shorter input
                "-y",
                narrated_output_path
            ]
            
            print("Adding narration to video...")
            try:
                subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
                print(f"✓ Successfully created video with narration: {narrated_output_path}")
                return narrated_output_path
            except subprocess.CalledProcessError as e:
                print("✗ Error adding narration to video")
                if e.stderr:
                    print("Error details: " + e.stderr.decode())
                return None

        except Exception as e:
            print(f"Error creating video with narration: {e}")
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

    def generate_speech(self, text, output_path):
        """
        Generate speech audio from text
        
        Parameters:
        - text: The text to convert to speech
        - output_path: Path to save the audio file
        
        Returns:
        - Path to the generated audio file if successful, None otherwise
        """
        print(f"Generating speech for text: '{text[:50]}...'")
        
        # Try different TTS engines in order of preference
        if GTTS_AVAILABLE:
            try:
                print("Using Google Text-to-Speech...")
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(output_path)
                print(f"✓ Speech generated and saved to {output_path}")
                return output_path
            except Exception as e:
                print(f"✗ Error using Google TTS: {e}")
        
        if PYTTSX3_AVAILABLE:
            try:
                print("Using pyttsx3 for speech generation...")
                engine = pyttsx3.init()
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                print(f"✓ Speech generated and saved to {output_path}")
                return output_path
            except Exception as e:
                print(f"✗ Error using pyttsx3: {e}")
        
        print("No text-to-speech engines available. Please install either gTTS or pyttsx3.")
        return None

    def get_audio_duration(self, audio_path):
        """
        Get the duration of an audio file using FFmpeg
        
        Parameters:
        - audio_path: Path to the audio file
        
        Returns:
        - Duration in seconds (float) or None if error
        """
        if not self.ffmpeg_available:
            print("FFmpeg not available. Cannot determine audio duration.")
            return None
        
        try:
            # Use FFprobe instead of FFmpeg for getting duration
            duration_cmd = [
                self.ffmpeg_path.replace("ffmpeg", "ffprobe"),  # Use ffprobe instead
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                audio_path
            ]
            
            print(f"Running command to get audio duration: {' '.join(duration_cmd)}")
            
            # Run the command and capture stdout
            result = subprocess.run(
                duration_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=False
            )
            
            # Parse the JSON output
            if result.stdout:
                try:
                    info = json.loads(result.stdout.decode())
                    if 'format' in info and 'duration' in info['format']:
                        duration = float(info['format']['duration'])
                        print(f"Audio duration detected: {duration:.2f} seconds")
                        return duration
                except json.JSONDecodeError:
                    print("Could not parse ffprobe JSON output")
            
            # If ffprobe fails, try a simpler approach with ffmpeg
            print("Trying alternative method to get duration...")
            alt_cmd = [
                self.ffmpeg_path,
                "-i", audio_path
            ]
            
            result = subprocess.run(
                alt_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=False
            )
            
            # Parse the output to find duration
            stderr = result.stderr.decode()
            print(f"FFmpeg output: {stderr}")
            
            # Look for Duration: 00:00:12.34
            duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                print(f"Audio duration detected (method 2): {total_seconds:.2f} seconds")
                return total_seconds
            
            print("Could not determine audio duration. Using default length.")
            # Return a default duration if we can't determine it
            return 30.0  # Default to 30 seconds
        
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            import traceback
            traceback.print_exc()
            # Return a default duration if we can't determine it
            return 30.0  # Default to 30 seconds

    def create_video(self, script, videos, output_filename=None):
        """
        Create a video by combining clips with the script and narration
        
        Parameters:
        - script: The script text to use for the video
        - videos: List of video information dictionaries from Pexels API
        - output_filename: Name for the output file (optional)
        """
        # Use our new method that matches video length to narration
        return self.create_video_with_narration(script, videos, output_filename)

    def add_captions_to_video(self, video_path, script_text, output_path=None):
        """
        Add captions to a video
        
        Parameters:
        - video_path: Path to the video file
        - script_text: Text to display as captions
        - output_path: Path for the output video (optional)
        
        Returns:
        - Path to the video with captions if successful, None otherwise
        """
        if not self.ffmpeg_available:
            print("FFmpeg not available. Cannot add captions.")
            return None
        
        if not output_path:
            # Generate output filename based on input
            output_path = video_path.replace('.mp4', '_captioned.mp4')
        
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Create a text file with the script
            text_file = os.path.join(temp_dir, "caption.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(script_text)
            
            # Try a simpler approach - use a scrolling text at the bottom
            # This is more reliable than trying to time individual chunks
            
            print("Adding scrolling caption to video...")
            
            # Get video duration to calculate scroll speed
            duration_cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0"
            ]
            
            try:
                result = subprocess.run(
                    duration_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    check=True
                )
                duration = float(result.stdout.decode().strip())
                print(f"Video duration: {duration:.2f} seconds")
            except:
                # If we can't get the duration, assume 30 seconds
                duration = 30.0
                print(f"Could not determine video duration, assuming {duration} seconds")
            
            # Break the script into shorter lines for better readability
            lines = []
            words = script_text.split()
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 40:  # Max 40 chars per line
                    lines.append(' '.join(current_line))
                    current_line = []
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Join lines with newlines
            formatted_text = '\\n'.join(lines)
            
            # Escape special characters
            formatted_text = formatted_text.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,").replace("\\", "\\\\")
            
            # Create a command with a simple text overlay
            caption_cmd = [
                self.ffmpeg_path,
                "-v", "warning",
                "-i", video_path,
                "-vf", (
                    f"drawtext=text='{formatted_text}':"
                    f"fontcolor=white:fontsize=24:box=1:"
                    f"boxcolor=black@0.8:boxborderw=5:"
                    f"x=(w-text_w)/2:y=h-th-50"
                ),
                "-c:a", "copy",
                "-y",
                output_path
            ]
            
            print(f"Adding caption to video...")
            
            # Run with minimal output
            subprocess.run(caption_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
            print(f"✓ Successfully added caption to video: {output_path}")
            return output_path
        
        except Exception as e:
            print(f"Error adding captions: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to the simplest possible method
            return self.add_simple_text_overlay(video_path, script_text, output_path)
        
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary files in {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")

    def add_simple_text_overlay(self, video_path, script_text, output_path):
        """
        Add a simple text overlay to the video
        
        Parameters:
        - video_path: Path to the video file
        - script_text: Text to display as overlay
        - output_path: Path for the output video
        
        Returns:
        - Path to the video with text overlay if successful, None otherwise
        """
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Get the first sentence or up to 50 characters
            first_sentence = re.split(r'(?<=[.!?])\s+', script_text)[0]
            short_text = first_sentence[:50] + "..." if len(first_sentence) > 50 else first_sentence
            
            # Escape special characters
            short_text = short_text.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,").replace("\\", "\\\\")
            
            # Create a simple drawtext filter with better styling
            text_cmd = [
                self.ffmpeg_path,
                "-v", "warning",
                "-i", video_path,
                "-vf", (
                    f"drawtext=text='{short_text}':"
                    f"fontcolor=white:fontsize=28:box=1:"
                    f"boxcolor=black@0.8:boxborderw=5:"
                    f"x=(w-text_w)/2:y=h-th-50"
                ),
                "-c:a", "copy",
                "-y",
                output_path
            ]
            
            print(f"Adding simple text overlay to video...")
            
            # Run with minimal output
            subprocess.run(text_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
            print(f"✓ Successfully added text overlay to video: {output_path}")
            return output_path
        
        except Exception as e:
            print(f"Error adding text overlay: {e}")
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

    def format_srt_time(self, seconds):
        """Format seconds as HH:MM:SS,mmm for SRT files"""
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds %= 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

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
            us_news = news_api.search_news(query="United States", max_results=8)
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
            headlines = news_api.get_top_headlines(country="us", max_results=8)
            
            if not headlines.empty:
                print("\nTop 8 news headlines in the United States:")
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
            rss_headlines = rss_scraper.get_top_headlines(limit=8)
            
            if not rss_headlines.empty:
                print("\nTop news headlines from Romanian sources:")
                for i, (_, article) in enumerate(rss_headlines.iterrows(), 1):
                    print(f"{i}. {article['title']} ({article['source']})")
                    if 'description' in article and article['description']:
                        print(f"   {article['description'][:100]}...")
                    print(f"   URL: {article['url']}")
                    print()
                
                articles_df = rss_headlines
                top_titles = rss_headlines["title"].tolist()[:8]
            else:
                print("No headlines found from Romanian RSS feeds.")
                print("Trying US news sources...")
                
                # Try US news sources
                us_rss_feeds = {
                    "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
                    "NPR": "https://feeds.npr.org/1001/rss.xml",
                    "Washington Post": "http://feeds.washingtonpost.com/rss/national",
                    "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                    "USA Today": "http://rssfeeds.usatoday.com/usatoday-NewsTopStories"
                }
                
                # Try each US RSS feed
                for feed_name, feed_url in us_rss_feeds.items():
                    try:
                        print(f"\nTrying US RSS feed: {feed_name}")
                        us_rss_parser = RSSFeedParser(feed_url)
                        us_feed_articles = us_rss_parser.get_articles(max_results=8)
                        
                        if not us_feed_articles.empty:
                            print(f"\nTop 8 articles from {feed_name}:")
                            for i, (_, article) in enumerate(us_feed_articles.iterrows(), 1):
                                print(f"{i}. {article['title']}")
                                print(f"   {article['description'][:100] if 'description' in article and article['description'] else ''}...")
                                print(f"   URL: {article['url']}")
                                print()
                            
                            articles_df = us_feed_articles
                            top_titles = us_feed_articles["title"].tolist()
                            break
                        else:
                            print(f"No articles found in {feed_name} feed.")
                    except Exception as e:
                        print(f"Error with {feed_name} RSS feed: {e}")
                
                # If still no articles, fall back to predefined topics
                if not top_titles:
                    print("No headlines found from US RSS feeds either.")
                    print("Falling back to predefined US news topics...")
                    us_topics = [
                        "US Politics", 
                        "US Economy", 
                        "US Sports", 
                        "US Health", 
                        "US Technology",
                        "World News",
                        "Entertainment News",
                        "Science News"
                    ]
                    
                    print("\nPredefined US news topics:")
                    for i, topic in enumerate(us_topics, 1):
                        print(f"{i}. {topic}")
                    
                    top_titles = us_topics
                
        except Exception as e:
            print(f"Error with RSS feeds: {e}")
            print("Falling back to predefined US news topics...")
            us_topics = [
                "US Politics", 
                "US Economy", 
                "US Sports", 
                "US Health", 
                "US Technology",
                "World News",
                "Entertainment News",
                "Science News"
            ]
            
            print("\nPredefined US news topics:")
            for i, topic in enumerate(us_topics, 1):
                print(f"{i}. {topic}")
            
            top_titles = us_topics

    # Print the final list of top titles
    print("\nFinal list of top titles:")
    for i, title in enumerate(top_titles[:8], 1):
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

                        article_category = "general" # Simplified category detection
                        # ... (keep category detection if desired, or remove)

                        enhanced_keywords = keyword_extractor.enhance_video_search(keywords, article_category)
                        print(f"Enhanced keywords for video search: {', '.join(enhanced_keywords)}")

                        # --- Simplified Video Search ---
                        target_video_count = 5
                        selected_videos_raw = []
                        footage_pool_urls = set() # Still useful for avoiding duplicates

                        print(f"\nSearching for up to {target_video_count} videos using keywords...")
                        keywords_to_search = enhanced_keywords[:target_video_count] # Use first 5 keywords

                        for keyword in keywords_to_search:
                            if len(selected_videos_raw) >= target_video_count:
                                break # Stop if we already have 5

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
                                        # else: # Optional debug
                                        #    print(f"  - Skipping video for '{keyword}' (duplicate URL: {video_url})")
                                    # else: # Optional debug
                                    #    if not video_url: print(f"  - Skipping video for '{keyword}' (no URL found in video_info)")
                                    #    else: print(f"  - Skipping video for '{keyword}' (URL not MP4: {video_url})")
                                if not video_added_for_keyword:
                                     print(f"  - Could not find a suitable unique video for '{keyword}' from results.")
                            else:
                                print(f"No videos found for keyword '{keyword}'")

                        # Fallback if not enough videos found
                        if len(selected_videos_raw) < target_video_count:
                            print(f"\nFound only {len(selected_videos_raw)} videos. Trying generic keywords for the remainder...")
                            generic_keywords = ["news", "world", "city", "technology", "business", "people"]
                            random.shuffle(generic_keywords) # Mix them up

                            for keyword in generic_keywords:
                                if len(selected_videos_raw) >= target_video_count:
                                    break # Stop if we have 5

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
                                            # else: # Optional debug
                                            #    print(f"  - Skipping generic video for '{keyword}' (duplicate URL: {video_url})")
                                        # else: # Optional debug
                                        #    if not video_url: print(f"  - Skipping generic video for '{keyword}' (no URL found in video_info)")
                                        #    else: print(f"  - Skipping generic video for '{keyword}' (URL not MP4: {video_url})")
                                    if not video_added_for_keyword:
                                        print(f"  - Could not find a suitable unique generic video for '{keyword}' from results.")
                                else:
                                    print(f"No generic videos found for keyword '{keyword}'")


                        if not selected_videos_raw:
                            print("\nError: Could not find any videos for the script. Cannot create video.")
                            continue # Go back to main menu

                        print(f"\nUsing {len(selected_videos_raw)} videos for the final video.")

                        # Create the video using the simplified list
                        print("\nCreating video...")
                        video_path = video_creator.create_video_with_narration(script_text, selected_videos_raw) # Pass the simplified list

                        if video_path:
                            # Add video to database
                            # Use the original enhanced keywords for DB logging, not just the ones we found videos for
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