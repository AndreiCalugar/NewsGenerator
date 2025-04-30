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
import inspect

# --- TTS Imports and Flags ---
try:
    # Import the client-based API instead of the older convenience functions
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs library not found. ElevenLabs TTS will be unavailable.")

try:
    # This should ONLY be the pyttsx3 import
    import pyttsx3  # For offline TTS
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("Warning: pyttsx3 not available. Offline TTS will be unavailable.")

try:
    from gtts import gTTS  # Google Text-to-Speech
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("Warning: gTTS not available. Google TTS will be unavailable.")
# --- End TTS Imports ---

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

# --- Add this near the other import blocks ---
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: OpenAI Whisper not available. Subtitle generation will be disabled.")

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
                has_subtitles INTEGER DEFAULT 0,
                FOREIGN KEY (script_id) REFERENCES scripts(id)
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
        """Add a video to the database"""
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
        except Exception as e:
            print(f"Error adding video to database: {e}")
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
                """, (limit,)
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
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check FFmpeg availability
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffmpeg_available = self.ffmpeg_path is not None
        if not self.ffmpeg_available:
            print("Warning: FFmpeg not found. Video creation will likely fail.")
            
        # --- Load ElevenLabs API Key ---
        self.elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        if ELEVENLABS_AVAILABLE and self.elevenlabs_api_key:
            try:
                # Create a client instance instead of setting the global API key
                self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
                print("ElevenLabs API key loaded and client created.")
            except Exception as e:
                print(f"Warning: Failed to initialize ElevenLabs client: {e}")
                self.elevenlabs_api_key = None
                self.elevenlabs_client = None
        elif ELEVENLABS_AVAILABLE:
            print("Warning: ELEVENLABS_API_KEY not found in .env file. ElevenLabs TTS will be unavailable.")
            self.elevenlabs_client = None
        else:
            self.elevenlabs_client = None
        # --- End ElevenLabs Key Loading ---

    def _find_ffmpeg(self):
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
        """
        Download a video from a URL to a local file.
        
        Parameters:
        - url: URL of the video to download
        - output_path: Path to save the downloaded video
        
        Returns:
        - True if successful, False otherwise
        """
        try:
            # If url is a dictionary with 'url' key, extract the actual URL
            if isinstance(url, dict) and 'url' in url:
                url = url['url']
                
            print(f"Downloading video from {url}...")
            
            # Using requests to download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify the file was downloaded successfully
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Video downloaded to {output_path}")
                return True
            else:
                print(f"Error: Downloaded file is empty or missing: {output_path}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error downloading video: {e}")
            return False
        except Exception as e:
            print(f"Error saving video: {e}")
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

    def create_video_with_narration(self, script_text, video_sources):
        """
        Create a video with narration and subtitles from multiple video files
        
        Parameters:
        - script_text: The text script for narration
        - video_sources: List of video sources, either URLs as strings or dictionaries with 'url' key
        
        Returns:
        - Path to the created video
        """
        if not video_sources:
            print("No video sources provided. Cannot create video.")
            return None
        
        if not self.ffmpeg_available:
            print("FFmpeg is not available. Cannot create video.")
            return None
        
        # Generate a unique filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"news_video_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        try:  # Main try block for the entire method
            # 1. Generate Narration & Get Duration
            print("Generating narration from script...")
            audio_path = os.path.join(temp_dir, "narration.mp3")
            if not self.generate_speech(script_text, audio_path):
                print("Failed to generate speech. Cannot create narrated video.")
                return None
            
            duration = self.get_audio_duration(audio_path)
            if not duration:
                print("Failed to get audio duration. Cannot create video.")
                return None
            print(f"Narration duration: {duration} seconds")
            
            # 2. Download Videos
            print(f"Downloading {len(video_sources)} videos...")
            downloaded_video_paths = []
            for i, video_source in enumerate(video_sources):
                # Extract URL from dictionary if needed
                if isinstance(video_source, dict) and 'url' in video_source:
                    video_url = video_source['url']
                else:
                    video_url = video_source  # Assume it's already a URL string
                    
                video_path = os.path.join(temp_dir, f"download_{i}.mp4")
                if self.download_video(video_url, video_path):
                    downloaded_video_paths.append(video_path)
            
            if not downloaded_video_paths:
                print("Failed to download any videos. Cannot create video.")
                return None
            
            print(f"Successfully downloaded {len(downloaded_video_paths)} videos.")
            
            # Save script to a text file for future reference
            script_path = output_path.replace('.mp4', '_script.txt')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_text)
            print(f"Script saved to {script_path}")
            
            # Calculate clips durations
            clip_count = len(downloaded_video_paths)
            clip_duration = duration / clip_count
            print(f"Each clip will be processed to fit {clip_duration:.2f} seconds.")
            
            # Process videos (trim and standardize)
            processed_videos = []
            for i, video_path in enumerate(downloaded_video_paths):
                print(f"Processing video {i+1}/{clip_count}...")
                processed_path = os.path.join(temp_dir, f"processed_{i}.mp4")
                success = self.process_video(video_path, processed_path, clip_duration)
                if success:
                    processed_videos.append(processed_path)
                    print(f"✓ Successfully processed video {i+1}")
                else:
                    print(f"✗ Failed to process video {i+1}")
            
            if not processed_videos:
                print("No videos were successfully processed. Cannot create video.")
                return None
            
            # Concatenate processed videos
            print("Concatenating videos...")
            concat_file_path = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file_path, 'w') as f:
                for video in processed_videos:
                    f.write(f"file '{video}'\n")
            
            # Using FFmpeg to concatenate
            concat_output = os.path.join(temp_dir, "concatenated.mp4")
            concat_cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file_path,
                "-c", "copy",
                "-y", concat_output
            ]
            
            try:
                subprocess.run(concat_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("✓ Videos concatenated successfully")
            except subprocess.CalledProcessError as e:
                print(f"Error concatenating videos: {e}")
                return None
            
            # Add narration using FFmpeg
            print("Adding narration to video...")
            try:
                # Normalize audio levels and add to video
                final_cmd = [
                    self.ffmpeg_path,
                    "-i", concat_output,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-y", output_path
                ]
                
                subprocess.run(final_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"✓ Successfully created video with narration: {output_path}")
                
                # After the narration file is created and before video processing:
                subtitle_path = None
                if WHISPER_AVAILABLE:
                    print("Generating subtitles with Whisper...")
                    segments = self.transcribe_audio(audio_path)
                    if segments:
                        subtitle_path = os.path.join(temp_dir, "subtitles.ass")
                        subtitle_path = self.generate_ass_subtitles(segments, subtitle_path)
                    else:
                        print("Whisper transcription failed, using script text for basic subtitles...")
                        # Create a simple subtitle file directly from the script text
                        subtitle_path = os.path.join(temp_dir, "simple_subtitles.srt")
                        self.generate_simple_subtitles(script_text, subtitle_path, duration)
                else:
                    print("Whisper not available, using script text for basic subtitles...")
                    subtitle_path = os.path.join(temp_dir, "simple_subtitles.srt")
                    self.generate_simple_subtitles(script_text, subtitle_path, duration)
                
                final_output_path = output_path
                if subtitle_path and os.path.exists(subtitle_path):
                    print("Attempting to add subtitles using traditional FFmpeg filters...")
                    subtitled_output_path = output_path.replace(".mp4", "_subtitled.mp4")
                    result = self.burn_subtitles(output_path, subtitle_path, subtitled_output_path)
                    
                    if result and result != output_path:  # Check if a new file was created
                        final_output_path = subtitled_output_path
                        print(f"✓ Video with burned-in subtitles created: {final_output_path}")
                    else:
                        print("Traditional subtitle burning failed, trying sequential captions...")
                        
                        # Try the sequential caption approach
                        seq_output_path = output_path.replace(".mp4", "_sequential.mp4")
                        seq_result = self.create_sequential_captions(output_path, script_text, seq_output_path)
                        
                        if seq_result and os.path.exists(seq_result):
                            final_output_path = seq_result
                            print(f"✓ Video with sequential captions created: {final_output_path}")
                        else:
                            print("Sequential captions failed, trying fixed caption as last resort...")
                            
                            # Fall back to the simple caption overlay as the last resort
                            caption_output_path = output_path.replace(".mp4", "_caption.mp4")
                            caption_result = self.create_caption_overlay(output_path, script_text, caption_output_path)
                            
                            if caption_result and os.path.exists(caption_result):
                                final_output_path = caption_result
                                print(f"✓ Video with fixed caption created: {final_output_path}")
                            else:
                                print("All subtitle methods failed, using original video")
                else:
                    print("No subtitle file available, trying direct text overlay...")
                    
                    # Try creating subtitles directly from script text
                    simplified_output_path = output_path.replace(".mp4", "_simple_subs.mp4")
                    simple_result = self.create_hardcoded_subtitles(output_path, script_text, simplified_output_path)
                    
                    if simple_result and os.path.exists(simple_result):
                        final_output_path = simple_result
                        print(f"✓ Video with direct text overlay created: {final_output_path}")
                    else:
                        print("Direct text overlay failed, using original video")
                
                return final_output_path
            
            except subprocess.CalledProcessError as e:
                print("✗ Error adding narration to video")
                print(f"Command output: {e.stderr}")
                return None
        
        except Exception as e:  # Main catch-all exception handler
            print(f"Error creating video with narration: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:  # Cleanup regardless of success or failure
            # Clean up
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary files in {temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")

    def generate_speech_elevenlabs(self, text, output_path, voice_id="DMyrgzQFny3JI1Y1paM5"):
        """
        Generates speech using the ElevenLabs API with the client-based approach.
        
        Parameters:
        - text: The text to synthesize.
        - output_path: The path to save the generated MP3 file.
        - voice_id: The ElevenLabs voice ID to use (default: "Donavan" - DMyrgzQFny3JI1Y1paM5).
                    Other common voices:
                    Adam:   pNInz6obpgDQGcFmaJgB
                    Antoni: ErXwobaYiN019PkySvjV
                    Rachel: 21m00Tcm4TlvDq8ikWAM
        
        Returns:
        - True if successful, False otherwise.
        """
        if not ELEVENLABS_AVAILABLE or not self.elevenlabs_client:
            print("ElevenLabs is not available or client not initialized.")
            return False
            
        print(f"Attempting TTS generation with ElevenLabs (Voice ID: {voice_id})...")
        try:
            # Generate speech using the client-based approach
            audio_response = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",  # For news content across languages
                output_format="mp3_44100_128",  # High quality for professional sound
                voice_settings=VoiceSettings(
                    stability=0.5,          # Balanced stability
                    similarity_boost=0.75,  # Higher similarity to reference voice
                    style=0.0,              # Neutral style for news
                    use_speaker_boost=True  # Enhance clarity
                )
            )
            
            # Write the audio stream to the output file
            with open(output_path, "wb") as f:
                # The response is a generator of audio chunks
                for chunk in audio_response:
                    if chunk:
                        f.write(chunk)
            
            # Verify the file was created successfully
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✓ ElevenLabs TTS generated successfully: {output_path}")
                return True
            else:
                print("✗ ElevenLabs completed but output file is empty or missing.")
                return False
            
        except Exception as e:
            # Handle errors
            print(f"✗ ElevenLabs TTS failed with error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check for specific error messages
            error_str = str(e).lower()
            if "quota" in error_str or "limit" in error_str:
                print("  (Possible quota exceeded)")
            elif "voice" in error_str and "not found" in error_str:
                print(f"  Error: Voice ID '{voice_id}' not found. Please check the ID on the ElevenLabs website.")
                
            return False

    def generate_speech(self, text, output_path):
        """
        Generates speech from text using available TTS engines.
        Tries ElevenLabs first, then pyttsx3, then gTTS.
        
        Parameters:
        - text: The text to synthesize.
        - output_path: The path to save the generated MP3 file.
        
        Returns:
        - True if speech was generated successfully by any method, False otherwise.
        """
        
        # --- Try ElevenLabs First ---
        if ELEVENLABS_AVAILABLE and self.elevenlabs_client:
            if self.generate_speech_elevenlabs(text, output_path):
                return True # Success with ElevenLabs
            else:
                print("ElevenLabs failed, trying next TTS engine...")
        # --- End ElevenLabs Attempt ---

        # --- Try pyttsx3 (Offline) ---
        if PYTTSX3_AVAILABLE:
            print("Attempting TTS generation with pyttsx3 (offline)...")
            try:
                engine = pyttsx3.init()
                # Optional: Configure voice, rate, volume
                # voices = engine.getProperty('voices')
                # engine.setProperty('voice', voices[0].id) # Change index for different voices
                # engine.setProperty('rate', 180) # Adjust speed
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                # Check if file was created and has size
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"✓ pyttsx3 TTS generated successfully: {output_path}")
                    return True
                else:
                    print("✗ pyttsx3 completed but output file is missing or empty.")
                    # Clean up potentially empty file
                    if os.path.exists(output_path): os.remove(output_path)
            except Exception as e:
                print(f"✗ pyttsx3 TTS failed: {e}")
        else:
            print("pyttsx3 not available, skipping.")
        # --- End pyttsx3 Attempt ---

        # --- Try gTTS (Online) ---
        if GTTS_AVAILABLE:
            print("Attempting TTS generation with gTTS (online)...")
            try:
                tts = gTTS(text=text, lang='en') # Specify language
                tts.save(output_path)
                # Check if file was created and has size
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"✓ gTTS generated successfully: {output_path}")
                    return True
                else:
                    print("✗ gTTS completed but output file is missing or empty.")
                     # Clean up potentially empty file
                    if os.path.exists(output_path): os.remove(output_path)
            except Exception as e:
                print(f"✗ gTTS TTS failed: {e}")
        else:
            print("gTTS not available, skipping.")
        # --- End gTTS Attempt ---

        print("✗ All TTS generation methods failed.")
        return False

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

    def transcribe_audio(self, audio_path):
        """
        Transcribe the narration audio using OpenAI's Whisper
        
        Parameters:
        - audio_path: Path to the audio file to transcribe
        
        Returns:
        - A list of segments with start time, end time, and text
        """
        if not WHISPER_AVAILABLE:
            print("Whisper not available. Cannot generate subtitles.")
            return None
        
        try:
            print("Loading Whisper model (this may take a moment)...")
            # Use the "tiny" or "base" model for faster processing, or "small"/"medium" for better accuracy
            model = whisper.load_model("base")
            
            print(f"Transcribing audio: {audio_path}")
            
            # Fix for FFmpeg path issue - explicitly set the FFmpeg command
            import os
            os.environ["PATH"] = os.environ["PATH"] + ";" + os.path.dirname(self.ffmpeg_path)
            
            # Provide more information about the audio file path
            if not os.path.exists(audio_path):
                print(f"Error: Audio file does not exist at {audio_path}")
                return None
                
            try:
                result = model.transcribe(audio_path, verbose=False)
            except Exception as e:
                print(f"Whisper transcription failed: {e}")
                print("Trying alternative approach with raw audio...")
                
                # Fallback approach: Convert MP3 to WAV first using our own FFmpeg
                wav_path = audio_path.replace('.mp3', '.wav')
                convert_cmd = [
                    self.ffmpeg_path,
                    "-i", audio_path,
                    "-ar", "16000",  # 16kHz sample rate (what Whisper expects)
                    "-ac", "1",      # mono
                    "-c:a", "pcm_s16le",  # 16-bit PCM
                    "-y", wav_path
                ]
                
                try:
                    subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print(f"Converted audio to WAV format for Whisper: {wav_path}")
                    
                    # Now try transcribing the WAV file
                    if os.path.exists(wav_path):
                        result = model.transcribe(wav_path, verbose=False)
                    else:
                        print(f"Error: WAV conversion failed, file not found at {wav_path}")
                        return None
                except Exception as conv_e:
                    print(f"Error converting audio to WAV: {conv_e}")
                    return None
            
            if not result or "segments" not in result:
                print("Transcription failed: No segments found")
                return None
            
            print(f"Transcription completed: {len(result['segments'])} segments")
            return result["segments"]
        
        except Exception as e:
            print(f"Error during transcription: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_ass_subtitles(self, segments, output_path):
        """
        Generate an ASS subtitle file from transcription segments
        
        Parameters:
        - segments: List of segments with start/end times and text
        - output_path: Path to save the ASS subtitle file
        
        Returns:
        - Path to the subtitle file or None if failed
        """
        if not segments:
            return None
        
        try:
            print(f"Generating ASS subtitle file: {output_path}")
            
            # ASS file header with improved styling
            header = """[Script Info]
Title: Auto-generated by AutoVid
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.5,1.5,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(header)
                
                # Write each dialogue line
                for i, segment in enumerate(segments):
                    start_time = self._format_timestamp(segment["start"])
                    end_time = self._format_timestamp(segment["end"])
                    text = segment["text"].strip()
                    
                    # Convert long lines into multiple lines for better readability
                    # (split at around 40 characters, on word boundaries)
                    if len(text) > 40:
                        words = text.split()
                        lines = []
                        current_line = ""
                        
                        for word in words:
                            if len(current_line) + len(word) + 1 > 40:
                                lines.append(current_line)
                                current_line = word
                            else:
                                if current_line:
                                    current_line += " " + word
                                else:
                                    current_line = word
                        
                        if current_line:
                            lines.append(current_line)
                        
                        text = "\\N".join(lines)  # \N is the ASS newline character
                    
                    dialogue_line = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
                    f.write(dialogue_line)
            
            if os.path.exists(output_path):
                print(f"✓ ASS subtitle file generated successfully: {output_path}")
                return output_path
            else:
                print("Failed to generate subtitle file")
                return None
        
        except Exception as e:
            print(f"Error generating subtitle file: {e}")
            return None
        
    def _format_timestamp(self, seconds):
        """
        Convert seconds to ASS timestamp format (h:mm:ss.cc)
        """
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        seconds = seconds % 60
        centiseconds = int((seconds - int(seconds)) * 100)
        seconds = int(seconds)
        
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def burn_subtitles(self, video_path, subtitle_path, output_path):
        """
        Burn subtitles onto a video using FFmpeg with improved path handling
        
        Parameters:
        - video_path: Path to the input video
        - subtitle_path: Path to the ASS subtitle file
        - output_path: Path to save the output video with subtitles
        
        Returns:
        - Path to the output video or None if failed
        """
        if not os.path.exists(video_path) or not os.path.exists(subtitle_path):
            print(f"Error: Video or subtitle file not found")
            return None
        
        try:
            print(f"Burning subtitles onto video...")
            
            # Get absolute paths to avoid ~1 short format issues
            video_path_abs = os.path.abspath(video_path)
            subtitle_path_abs = os.path.abspath(subtitle_path)
            output_path_abs = os.path.abspath(output_path)
            
            # Use a simpler subtitle filter that is more reliable
            subtitle_filter = f"subtitles='{subtitle_path_abs.replace(chr(92), '/')}'"
            
            # Alternative command using a more reliable subtitles filter
            cmd = [
                self.ffmpeg_path,
                "-i", video_path_abs,
                "-vf", subtitle_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "copy",
                "-y", output_path_abs
            ]
            
            print(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Execute the command
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                print(f"✓ Video with subtitles created successfully: {output_path}")
                return output_path
            else:
                print("Failed to create video with subtitles")
                return None
        
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            if e.stderr:
                error_text = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                print(f"FFmpeg Error: {error_text}")
                
            # If the above approach fails, try with a simpler SRT format
            try:
                print("Trying alternative subtitle approach...")
                # Convert ASS to SRT first
                srt_path = subtitle_path.replace('.ass', '.srt')
                self._convert_ass_to_srt(subtitle_path, srt_path)
                
                if os.path.exists(srt_path):
                    # Use a more basic subtitle filter
                    cmd = [
                        self.ffmpeg_path,
                        "-i", video_path_abs,
                        "-vf", f"subtitles='{os.path.abspath(srt_path).replace(chr(92), '/')}'",
                        "-c:v", "libx264",
                        "-preset", "fast", 
                        "-crf", "23",
                        "-c:a", "copy",
                        "-y", output_path_abs
                    ]
                    
                    print(f"Running alternative FFmpeg command: {' '.join(cmd)}")
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if os.path.exists(output_path):
                        print(f"✓ Video with subtitles created successfully (alternative method): {output_path}")
                        return output_path
                
                print("Alternative subtitle approach also failed")
            except Exception as alt_e:
                print(f"Alternative subtitle method failed: {alt_e}")
            
            # Return the original video if subtitle burning fails
            print("Returning original video without subtitles")
            return video_path
        
        except Exception as e:
            print(f"Error burning subtitles: {e}")
            # Return the original video if subtitle burning fails
            print("Returning original video without subtitles")
            return video_path

    def _convert_ass_to_srt(self, ass_path, srt_path):
        """
        Convert ASS subtitle file to SRT format using our segments
        """
        try:
            # Read the ASS file to extract text and timing
            with open(ass_path, 'r', encoding='utf-8') as f:
                ass_content = f.readlines()
            
            # Find the dialogue lines
            dialogue_lines = [line for line in ass_content if line.startswith('Dialogue:')]
            
            # Write SRT format
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, line in enumerate(dialogue_lines):
                    parts = line.split(',', 9)  # Split into at most 10 parts
                    if len(parts) >= 10:
                        start_time = parts[1]
                        end_time = parts[2]
                        text = parts[9].strip()
                        
                        # Convert ASS time format to SRT
                        srt_start = self._ass_to_srt_time(start_time)
                        srt_end = self._ass_to_srt_time(end_time)
                        
                        # Remove any ASS formatting
                        text = re.sub(r'{.*?}', '', text)
                        
                        # Write SRT entry
                        f.write(f"{i+1}\n")
                        f.write(f"{srt_start} --> {srt_end}\n")
                        f.write(f"{text}\n\n")
            
            return True
        except Exception as e:
            print(f"Error converting ASS to SRT: {e}")
            return False

    def _ass_to_srt_time(self, ass_time):
        """
        Convert ASS time format (h:mm:ss.cc) to SRT format (hh:mm:ss,mmm)
        """
        h, m, rest = ass_time.split(':', 2)
        s, cs = rest.split('.')
        
        # Convert to milliseconds
        ms = int(cs) * 10
        
        return f"{h.zfill(2)}:{m.zfill(2)}:{s.zfill(2)},{ms:03d}"

    def process_video(self, input_path, output_path, target_duration):
        """
        Process a video to fit a target duration.
        
        Parameters:
        - input_path: Path to the input video
        - output_path: Path to save the processed video
        - target_duration: Target duration in seconds
        
        Returns:
        - True if successful, False otherwise
        """
        if not os.path.exists(input_path):
            print(f"Error: Input video not found: {input_path}")
            return False
            
        try:
            # FFmpeg command to scale, set duration (padding if needed), remove audio
            process_cmd = [
                self.ffmpeg_path,
                "-i", input_path,
                "-vf", f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,tpad=stop_mode=clone:stop_duration={target_duration+0.1}",  # Scale, pad, set fps, pad end
                "-t", str(target_duration),  # Trim to exactly target_duration
                "-an",  # Remove original audio
                "-c:v", "libx264",  # Re-encode
                "-preset", "fast",
                "-crf", "23",
                "-y",
                output_path
            ]
            
            # Execute the command
            subprocess.run(process_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Verify the file was created successfully
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print(f"Error: Processed video is empty or missing: {output_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Error processing video: {e}")
            if e.stderr:
                error_text = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                print(f"FFmpeg Error: {error_text}")
            return False
        except Exception as e:
            print(f"Unexpected error processing video: {e}")
            return False

    def create_simple_subtitled_video(self, video_path, subtitle_text, output_path):
        """
        A simpler approach to add basic hardcoded subtitles using drawtext filter
        
        Parameters:
        - video_path: Path to input video
        - subtitle_text: Plain text of subtitles
        - output_path: Path to save output video
        
        Returns:
        - Path to output video or None if failed
        """
        try:
            # Split subtitle text into chunks (about 40 chars each)
            words = subtitle_text.split()
            chunks = []
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= 40:
                    if current_chunk:
                        current_chunk += " " + word
                    else:
                        current_chunk = word
                else:
                    chunks.append(current_chunk)
                    current_chunk = word
                    
            if current_chunk:
                chunks.append(current_chunk)
            
            # Calculate approximate duration for each chunk
            total_duration = self.get_video_duration(video_path)
            chunk_duration = total_duration / len(chunks) if chunks else 0
            
            # Create a temporary subtitle file with timecodes
            temp_sub_path = os.path.join(os.path.dirname(output_path), "temp_subs.srt")
            with open(temp_sub_path, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks):
                    start_time = i * chunk_duration
                    end_time = (i + 1) * chunk_duration
                    
                    # Write SRT format
                    f.write(f"{i+1}\n")
                    f.write(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}\n")
                    f.write(f"{chunk}\n\n")
            
            # Use FFmpeg with the simpler subtitles filter
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vf", f"subtitles='{temp_sub_path.replace(chr(92), '/')}'",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "copy",
                "-y", output_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Clean up temporary file
            if os.path.exists(temp_sub_path):
                os.remove(temp_sub_path)
            
            if os.path.exists(output_path):
                return output_path
            return None
        
        except Exception as e:
            print(f"Error creating simple subtitled video: {e}")
            return None
    
    def _format_srt_time(self, seconds):
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"
    
    def get_video_duration(self, video_path):
        """Get duration of a video file using FFmpeg"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
            ]
            
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            duration = float(result.stdout.decode().strip())
            return duration
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0

    def generate_simple_subtitles(self, text, output_path, duration):
        """
        Generate a simple SRT subtitle file from text, splitting it evenly across the duration
        
        Parameters:
        - text: The text to convert to subtitles
        - output_path: Path to save the subtitle file
        - duration: Duration of the video in seconds
        
        Returns:
        - Path to the subtitle file or None if failed
        """
        try:
            # Split the text into chunks of approximately 40 characters each
            words = text.split()
            chunks = []
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= 40:
                    if current_chunk:
                        current_chunk += " " + word
                    else:
                        current_chunk = word
                else:
                    chunks.append(current_chunk)
                    current_chunk = word
            
            if current_chunk:
                chunks.append(current_chunk)
            
            # Calculate time per chunk
            chunk_count = len(chunks)
            time_per_chunk = duration / chunk_count if chunk_count > 0 else duration
            
            # Write the SRT file
            with open(output_path, "w", encoding="utf-8") as f:
                for i, chunk in enumerate(chunks):
                    start_time = i * time_per_chunk
                    end_time = (i + 1) * time_per_chunk
                    
                    # Format times as SRT timestamps
                    start_str = self._format_srt_time(start_time)
                    end_str = self._format_srt_time(end_time)
                    
                    # Write the subtitle entry
                    f.write(f"{i+1}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{chunk}\n\n")
            
            if os.path.exists(output_path):
                print(f"✓ Simple subtitle file generated successfully: {output_path}")
                return output_path
            else:
                print("Failed to generate simple subtitle file")
                return None
            
        except Exception as e:
            print(f"Error generating simple subtitles: {e}")
            return None

    def create_hardcoded_subtitles(self, video_path, script_text, output_path):
        """
        A very simple approach that adds text directly to the video using drawtext filter
        
        Parameters:
        - video_path: Path to the input video
        - script_text: The text to show as subtitles
        - output_path: Path to save the output video
        
        Returns:
        - Path to the output video or None if failed
        """
        try:
            print("Using direct text overlay approach for subtitles...")
            
            # Split the script into shorter lines
            lines = []
            words = script_text.split()
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= 40:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Maximum number of lines to show at once
            max_visible_lines = 2
            
            # Calculate how many frames to show each line
            video_duration = self.get_video_duration(video_path)
            if video_duration <= 0:
                print("Could not determine video duration, using default 30 seconds")
                video_duration = 30
                
            frames_per_line = int((video_duration * 30) / len(lines))  # Assuming 30fps
            
            # Create a temporary VTT file (simpler format)
            temp_dir = os.path.dirname(output_path)
            vtt_path = os.path.join(temp_dir, "simple_subs.vtt")
            
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                
                for i, line in enumerate(lines):
                    start_time = i * (video_duration / len(lines))
                    end_time = (i + 1) * (video_duration / len(lines))
                    
                    # Format as VTT timestamps
                    start_str = self._format_vtt_time(start_time)
                    end_str = self._format_vtt_time(end_time)
                    
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{line}\n\n")
            
            # Use the drawtext filter for each line
            drawtext_filters = []
            for i in range(max_visible_lines):
                y_position = f"h-{100 + (i * 40)}"  # Position from bottom
                drawtext_filter = (
                    f"drawtext=text='':fontfile=/Windows/Fonts/arial.ttf:fontsize=24:"
                    f"fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5:"
                    f"x=(w-text_w)/2:y={y_position}:"
                    f"enable='between(t,0,{video_duration})'"
                )
                drawtext_filters.append(drawtext_filter)
            
            # Create a very simple filter to add text at the bottom
            simple_filter = "drawtext=text='Loading subtitles...':fontfile=/Windows/Fonts/arial.ttf:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-100"
            
            # Create the FFmpeg command
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vf", simple_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "copy",
                "-y", output_path
            ]
            
            print(f"Running simplified subtitle command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                print(f"✓ Video with basic text overlay created: {output_path}")
                return output_path
            else:
                print("Failed to create video with text overlay")
                return None
                
        except Exception as e:
            print(f"Error creating hardcoded subtitles: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _format_vtt_time(self, seconds):
        """Format seconds as WebVTT timestamp (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{msecs:03d}"

    def create_subtitles_with_moviepy(self, video_path, script_text, output_path):
        """
        Create subtitles using MoviePy (if available)
        
        Parameters:
        - video_path: Path to the input video
        - script_text: The text script for narration
        - output_path: Path to save the output video
        
        Returns:
        - Path to the output video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            print("MoviePy not available for subtitle creation")
            return None
        
        try:
            from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
            
            print("Creating subtitles with MoviePy...")
            
            # Load the video
            video = VideoFileClip(video_path)
            
            # Split the script into parts
            parts = []
            sentences = script_text.split('. ')
            total_words = sum(len(s.split()) for s in sentences)
            words_per_second = total_words / video.duration
            
            # Break the script into chunks with timing
            position = 0
            for sentence in sentences:
                words = sentence.split()
                duration = len(words) / words_per_second
                parts.append({
                    'text': sentence + '.',
                    'start': position,
                    'duration': duration
                })
                position += duration
            
            # Create text clips for each part
            subtitle_clips = []
            for part in parts:
                text_clip = (TextClip(part['text'], fontsize=24, font='Arial', color='white', 
                                      bg_color='black', stroke_color='black', stroke_width=1,
                                      method='caption', align='center', size=(video.w * 0.8, None))
                              .set_position(('center', 'bottom'))
                              .set_start(part['start'])
                              .set_duration(part['duration']))
                subtitle_clips.append(text_clip)
            
            # Add subtitles to the video
            final_video = CompositeVideoClip([video] + subtitle_clips)
            
            # Write the result
            final_video.write_videofile(output_path, 
                                        codec='libx264', 
                                        audio_codec='aac', 
                                        temp_audiofile='temp-audio.m4a', 
                                        remove_temp=True,
                                        fps=video.fps)
            
            # Close the video objects
            video.close()
            final_video.close()
            
            if os.path.exists(output_path):
                print(f"✓ Video with MoviePy subtitles created: {output_path}")
                return output_path
            else:
                print("Failed to create video with MoviePy subtitles")
                return None
        
        except Exception as e:
            print(f"Error creating MoviePy subtitles: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_text_overlay_video(self, video_path, script_text, output_path):
        """
        Create a video with synchronized text overlays using drawtext filters
        
        Parameters:
        - video_path: Path to the input video
        - script_text: Text to display as subtitles
        - output_path: Path to save the output video
        
        Returns:
        - Path to the output video or None if failed
        """
        try:
            print("Creating video with synchronized text overlays...")
            
            # Get video duration
            try:
                # Use ffprobe to get duration more reliably
                cmd = [
                    os.path.join(os.path.dirname(self.ffmpeg_path), "ffprobe"),
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration = float(result.stdout.strip())
                print(f"Video duration: {duration} seconds")
            except Exception as e:
                print(f"Error getting duration with ffprobe: {e}")
                # Fallback to a default duration
                duration = 20
                print(f"Using default duration: {duration} seconds")
            
            # Split the script into sentences
            sentences = re.split(r'(?<=[.!?])\s+', script_text)
            
            # Calculate time per sentence
            sentence_count = len(sentences)
            time_per_sentence = duration / sentence_count
            
            # Prepare drawtext filters for each sentence
            drawtext_filters = []
            for i, sentence in enumerate(sentences):
                # Clean the sentence to avoid FFmpeg command issues
                clean_text = sentence.replace("'", "'").replace('"', '\\"').replace(':', '\\:').replace(',', '\\,')
                
                start_time = i * time_per_sentence
                end_time = (i + 1) * time_per_sentence
                
                # Create a drawtext filter for this sentence
                filter_text = (
                    f"drawtext=text='{clean_text}':"
                    f"fontfile=/Windows/Fonts/arial.ttf:fontsize=24:"
                    f"fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=5:"
                    f"x=(w-text_w)/2:y=h-100:"
                    f"enable='between(t,{start_time},{end_time})'"
                )
                drawtext_filters.append(filter_text)
            
            # Combine all drawtext filters with commas
            filter_complex = ",".join(drawtext_filters)
            
            # Create tempfiles for the complex filter to avoid command line length issues
            filter_file = os.path.join(os.path.dirname(output_path), "filter.txt")
            with open(filter_file, 'w', encoding='utf-8') as f:
                f.write(filter_complex)
            
            # Run FFmpeg with the filter complex
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-filter_complex_script", filter_file,
                "-c:v", "libx264",
                "-preset", "fast", 
                "-crf", "23",
                "-c:a", "copy",
                "-y", output_path
            ]
            
            print(f"Running FFmpeg with filter_complex_script...")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Clean up the filter file
            if os.path.exists(filter_file):
                os.remove(filter_file)
            
            if os.path.exists(output_path):
                print(f"✓ Video with synchronized text overlays created: {output_path}")
                return output_path
            else:
                print("Failed to create video with text overlays")
                return None
        
        except Exception as e:
            print(f"Error creating text overlay video: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_caption_overlay(self, video_path, script_text, output_path):
        """
        A super simple approach that just adds a fixed caption to the video
        
        Parameters:
        - video_path: Path to the input video
        - script_text: Text for the caption
        - output_path: Path to save the output video
        
        Returns:
        - Path to the output video or None if failed
        """
        try:
            print("Creating video with fixed caption overlay...")
            
            # Truncate and clean the script text to a reasonable length
            if len(script_text) > 120:
                # Take first 117 characters and add "..."
                script_text = script_text[:117] + "..."
            
            # Clean the text to avoid FFmpeg command issues
            clean_text = script_text.replace("'", "'").replace('"', '\\"').replace(':', '\\:').replace(',', '\\,')
            
            # Create a simple drawtext filter
            filter_text = (
                f"drawtext=text='{clean_text}':"
                f"fontfile=/Windows/Fonts/arial.ttf:fontsize=20:"
                f"fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=5:"
                f"x=(w-text_w)/2:y=h-80"
            )
            
            # Run FFmpeg with the simple filter
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vf", filter_text,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23", 
                "-c:a", "copy",
                "-y", output_path
            ]
            
            print(f"Running simple caption overlay command...")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                print(f"✓ Video with caption overlay created: {output_path}")
                return output_path
            else:
                print("Failed to create video with caption overlay")
                return None
                
        except Exception as e:
            print(f"Error creating caption overlay: {e}")
            return None

    def create_sequential_captions(self, video_path, script_text, output_path):
        """
        Create a video with multiple sequential captions using a chain of simpler filters
        
        Parameters:
        - video_path: Path to input video
        - script_text: Text to be displayed as captions
        - output_path: Path to save output video
        
        Returns:
        - Path to output video or None if failed
        """
        try:
            print("Creating video with sequential caption overlays...")
            
            # Get video duration
            try:
                probe_cmd = [
                    os.path.join(os.path.dirname(self.ffmpeg_path), "ffprobe"),
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    os.path.abspath(video_path)
                ]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                if probe_result.returncode == 0:
                    duration = float(probe_result.stdout.strip())
                    print(f"Video duration: {duration} seconds")
                else:
                    print(f"Error running ffprobe: {probe_result.stderr}")
                    duration = 20.0  # Default duration
            except Exception as e:
                print(f"Error getting video duration: {e}")
                duration = 20.0  # Default duration
                
            # Split text into sentences or chunks
            lines = []
            if len(script_text) > 150:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', script_text)
                
                # Now split long sentences into multiple lines
                for sentence in sentences:
                    if len(sentence) > 70:  # If sentence is too long, split it further
                        words = sentence.split()
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 <= 70:
                                if current_line:
                                    current_line += " " + word
                                else:
                                    current_line = word
                            else:
                                lines.append(current_line)
                                current_line = word
                        if current_line:
                            lines.append(current_line)
                    else:
                        lines.append(sentence)
            else:
                # Just use the whole script as a single caption
                lines.append(script_text)
            
            # Calculate time per line
            if len(lines) > 0:
                time_per_line = duration / len(lines)
            else:
                print("No lines to display")
                return None
            
            # Create a sequence of temporary videos, each with a single caption
            temp_videos = []
            base_name = os.path.splitext(output_path)[0]
            
            for i, line in enumerate(lines):
                # Clean the line for FFmpeg
                clean_line = line.replace("'", "'").replace('"', '\\"').replace(':', '\\:').replace(',', '\\,')
                
                # Create a temporary output file for this segment
                temp_output = f"{base_name}_temp_{i}.mp4"
                temp_videos.append(temp_output)
                
                # Calculate start and end times for this caption
                start_time = i * time_per_line
                end_time = (i + 1) * time_per_line
                segment_duration = end_time - start_time
                
                # Create filter for this segment
                if i == 0:
                    # For the first segment, use the original video from start
                    filter_text = (
                        f"drawtext=text='{clean_line}':"
                        f"fontfile=/Windows/Fonts/arial.ttf:fontsize=24:"
                        f"fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=5:"
                        f"x=(w-text_w)/2:y=h-100"
                    )
                    
                    # Create the segment with the caption
                    segment_cmd = [
                        self.ffmpeg_path,
                        "-i", video_path,
                        "-vf", filter_text,
                        "-ss", "0",
                        "-t", str(segment_duration),
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-crf", "23",
                        "-c:a", "copy",
                        "-y", temp_output
                    ]
                else:
                    # For subsequent segments, use the original video from appropriate offset
                    filter_text = (
                        f"drawtext=text='{clean_line}':"
                        f"fontfile=/Windows/Fonts/arial.ttf:fontsize=24:"
                        f"fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=5:"
                        f"x=(w-text_w)/2:y=h-100"
                    )
                    
                    # Create the segment with the caption
                    segment_cmd = [
                        self.ffmpeg_path,
                        "-i", video_path,
                        "-vf", filter_text,
                        "-ss", str(start_time),
                        "-t", str(segment_duration),
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-crf", "23",
                        "-c:a", "copy",
                        "-y", temp_output
                    ]
                
                print(f"Creating segment {i+1}/{len(lines)} with caption: {line[:30]}...")
                try:
                    subprocess.run(segment_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if not os.path.exists(temp_output) or os.path.getsize(temp_output) == 0:
                        print(f"Failed to create segment {i+1}, using simplified approach")
                        return self.create_caption_overlay(video_path, script_text, output_path)
                except subprocess.CalledProcessError as e:
                    print(f"Error creating segment {i+1}: {e}")
                    # If any segment fails, fall back to the basic caption
                    return self.create_caption_overlay(video_path, script_text, output_path)
            
            # Now concatenate all segments
            concat_file = f"{base_name}_concat.txt"
            with open(concat_file, 'w', encoding='utf-8') as f:
                for temp_video in temp_videos:
                    f.write(f"file '{os.path.abspath(temp_video)}'\n")
            
            # Run FFmpeg concat command to join all segments
            concat_cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-y", output_path
            ]
            
            print("Concatenating all segments...")
            try:
                subprocess.run(concat_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                print(f"Error concatenating segments: {e}")
                # If concatenation fails, fall back to the basic caption
                return self.create_caption_overlay(video_path, script_text, output_path)
            
            # Clean up temporary files
            for temp_video in temp_videos:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            if os.path.exists(output_path):
                print(f"✓ Video with sequential captions created: {output_path}")
                return output_path
            else:
                print("Failed to create video with sequential captions")
                return self.create_caption_overlay(video_path, script_text, output_path)
        
        except Exception as e:
            print(f"Error creating sequential captions: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to the basic caption method
            return self.create_caption_overlay(video_path, script_text, output_path)

    def debug_ffmpeg_command(self, cmd):
        """
        Run an FFmpeg command with detailed logging to help diagnose issues
        
        Parameters:
        - cmd: FFmpeg command list
        
        Returns:
        - Success flag, stdout, stderr
        """
        print("\n--- DEBUG: FFmpeg Command ---")
        print("Command: " + " ".join(cmd))
        
        # Check if all files in the command exist
        for i, item in enumerate(cmd):
            if i > 0 and (item.endswith('.mp4') or item.endswith('.txt') or item.endswith('.srt')):
                if os.path.exists(item):
                    file_size = os.path.getsize(item)
                    print(f"File exists: {item} (Size: {file_size} bytes)")
                else:
                    print(f"WARNING: File does not exist: {item}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"Return code: {result.returncode}")
            
            if result.stdout:
                print("--- STDOUT ---")
                print(result.stdout)
            
            if result.stderr:
                print("--- STDERR ---")
                print(result.stderr)
            
            return result.returncode == 0, result.stdout, result.stderr
        
        except Exception as e:
            print(f"Exception running command: {e}")
            return False, "", str(e)

    def create_video_from_text(self, title, text_content, output_dir=None):
        """
        Create a video directly from input text
        """
        try:
            print(f"Creating video from text: {title}")
            print(f"Text content length: {len(text_content)} characters")
            
            # Step 1: Generate script from the text content
            print("Generating script from text...")
            script_generator = ScriptGenerator()
            script = script_generator.generate_script(title, text_content)
            
            if not script:
                print("Failed to generate script from text content")
                return None, "Failed to generate script"
                
            print("-" * 50)
            print("Generated script:")
            print(script)
            print("-" * 50)
            
            # Step 2: Extract keywords
            print("Extracting keywords from script...")
            keyword_extractor = KeywordExtractor()
            
            # Handle different parameter signatures
            params = inspect.signature(keyword_extractor.extract_keywords).parameters
            if len(params) == 3:  # If it needs two arguments (plus self)
                keywords = keyword_extractor.extract_keywords(title, text_content)
            else:
                keywords = keyword_extractor.extract_keywords(script)
            
            print(f"Keywords: {', '.join(keywords)}")
            
            # Enhance keywords for better video results - same as in option 2
            enhanced_keywords = keyword_extractor.enhance_video_search(keywords, "general")
            print(f"Enhanced keywords for video search: {', '.join(enhanced_keywords)}")
            
            # Step 3: Setup output directory
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not output_dir:
                output_dir = os.path.join(self.output_dir, f"text2video_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the script to a file
            script_file = os.path.join(output_dir, "script.txt")
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(script)
            
            # Step 4: Search for videos - IDENTICAL to option 2
            target_video_count = 5
            selected_videos_raw = []
            footage_pool_urls = set() 
            
            print(f"\nSearching for up to {target_video_count} videos using keywords...")
            keywords_to_search = enhanced_keywords[:target_video_count]
            
            pexels_api = PexelsAPI()
            for keyword in keywords_to_search:
                if len(selected_videos_raw) >= target_video_count:
                    break  # Stop if we already have enough videos
                    
                print(f"Searching Pexels for videos with query: '{keyword}'...")
                videos = pexels_api.search_videos(keyword, per_page=3)
                
                if videos:
                    for video in videos:
                        video_url = video.get('url')
                        if video_url and video_url not in footage_pool_urls:
                            selected_videos_raw.append({
                                "url": video_url,
                                "keyword": keyword
                            })
                            footage_pool_urls.add(video_url)
                            print(f"Added video for '{keyword}': {video_url}")
                            break  # Just get one video per keyword
            
            # Step 5: Generate speech from script
            print("\nGenerating speech from script...")
            audio_file = os.path.join(output_dir, "narration.mp3")
            self.generate_speech(script, audio_file)
            
            # Step 6: Create the final video - EXACTLY like option 2 does
            if not selected_videos_raw:
                print("No videos found. Cannot create video.")
                return None, "No videos found for keywords"
            
            print(f"\nCreating video with {len(selected_videos_raw)} footage clips...")
            final_video = self.create_video_with_narration(script, selected_videos_raw)
            
            if final_video and os.path.exists(final_video):
                print(f"\nVideo created successfully: {final_video}")
                
                # Step 7: Create vertical version for social media
                try:
                    print("\nCreating vertical version for social media...")
                    vertical_path = final_video.replace('.mp4', '_vertical.mp4')
                    
                    cmd = [
                        "ffmpeg",
                        "-i", final_video,
                        "-vf", "scale=720:-2,pad=720:1280:(ow-iw)/2:(oh-ih)/2:black",
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-c:a", "copy",
                        "-y", vertical_path
                    ]
                    
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if os.path.exists(vertical_path):
                        print(f"Vertical video created: {vertical_path}")
                        return final_video, None, vertical_path
                    else:
                        # Return just the horizontal version if vertical fails
                        return final_video, None
                except Exception as e:
                    print(f"Error creating vertical video: {e}")
                    return final_video, None
            else:
                return None, "Failed to create video"
        
        except Exception as e:
            import traceback
            print(f"Error in create_video_from_text: {e}")
            traceback.print_exc()
            return None, str(e)

    # 1. First, add this new method to convert videos to vertical format
    def convert_to_vertical_video(self, input_file, output_file=None):
        """
        Convert a landscape video to vertical format (9:16) for social media
        
        Parameters:
        - input_file: Path to input video file
        - output_file: Path to output vertical video (if None, will use input_file with _vertical suffix)
        
        Returns:
        - Path to the vertical video file
        """
        try:
            if output_file is None:
                base, ext = os.path.splitext(input_file)
                output_file = f"{base}_vertical{ext}"
            
            print(f"Converting video to vertical format for social media...")
            
            # Use FFmpeg to convert to vertical format
            # This scales the video to fit in a 9:16 aspect ratio, centering it and adding black bars
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-vf", "scale=-1:1280,boxblur=20:5,scale=720:1280,setsar=1:1[bg];[0:v]scale=-2:720[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "copy",
                "-y", output_file
            ]
            
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_file):
                print(f"✓ Vertical video created: {output_file}")
                return output_file
            else:
                print("Failed to create vertical video")
                return None
        except Exception as e:
            print(f"Error creating vertical video: {e}")
            return None

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
            print("2. Download videos for an article (MoviePy not available)")
            print("3. View recent scripts")
            print("4. View recent videos")
            print("5. Create video from custom text")  # Add this new option
            print("6. Exit")  # Change from 5 to 6
            
            choice = input("\nEnter your choice (1-6): ")  # Update prompt to 1-6
            
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
            
            elif choice == "5":  # Create video from custom text
                print("\n--- CREATE VIDEO FROM CUSTOM TEXT ---")
                
                # Get title for the video
                title = input("Enter a title for your video: ")
                
                # Get the custom text
                print("\nEnter your text (type 'END' on a new line when finished):")
                text_lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    text_lines.append(line)
                
                custom_text = "\n".join(text_lines)
                
                if not custom_text.strip():
                    print("No text entered. Returning to main menu.")
                    continue
                
                print(f"\nCreating video from text with title: {title}")
                print(f"Text length: {len(custom_text)} characters")
                
                # Confirm with the user
                confirm = input("\nProceed with video creation? (y/n): ")
                if confirm.lower() != "y":
                    print("Video creation cancelled.")
                    continue
                
                # Create the video
                print("\nGenerating video, this may take some time...")
                
                # Call our method with proper handling of returned values
                result = video_creator.create_video_from_text(title, custom_text)
                
                # Check what was returned
                if len(result) == 2:
                    video_path, error = result
                    vertical_path = None
                else:
                    video_path, error, vertical_path = result
                
                if video_path and os.path.exists(video_path):
                    print(f"\nVideo created successfully!")
                    print(f"Video saved to: {video_path}")
                    
                    if vertical_path and os.path.exists(vertical_path):
                        print(f"Vertical video for social media saved to: {vertical_path}")
                    
                    # Add to database
                    try:
                        video_id = int(datetime.now().strftime("%Y%m%d%H%M%S"))
                        
                        # Extract keywords for database
                        keywords = keyword_extractor.extract_keywords(title, custom_text)
                        
                        # Create video path string
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
                                custom_text,
                                video_path_str,
                                ",".join(keywords),
                                datetime.now().isoformat()
                            )
                        )
                        db.conn.commit()
                        print(f"Video saved to database with ID: {video_id}")
                    except Exception as e:
                        print(f"Error saving to database: {e}")
                else:
                    print(f"\nFailed to create video: {error}")
            
            elif choice == "6":  # Change from 5 to 6
                print("Exiting program.")
                break
            
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")  # Update range
    
    except Exception as e:
        print(f"Error in main menu: {e}")
    
    # Close database connection
    db.close()
    print("Program completed.")