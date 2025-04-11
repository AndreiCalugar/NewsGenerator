import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
import sqlite3
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GNewsAPI:
    def __init__(self, api_key=None):
        # Use the provided API key or try to get from environment
        self.api_key = api_key or os.environ.get("GNEWS_API_KEY")
        if not self.api_key:
            raise ValueError("GNews API key is required")
        self.base_url = "https://gnews.io/api/v4"
    
    def get_top_headlines(self, country="ro", language="ro", max_results=5):
        """
        Get top headlines from Romania (or another country).
        
        Parameters:
        - country: Two-letter ISO 3166-1 country code (default: 'ro' for Romania)
        - language: Two-letter ISO 639-1 language code (default: 'ro' for Romanian)
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
    
    def search_news(self, query, language="ro", country="ro", max_results=5):
        """
        Search for news articles with a specific query.
        
        Parameters:
        - query: Keywords or phrases to search for
        - language: Two-letter ISO 639-1 language code (default: 'ro' for Romanian)
        - country: Two-letter ISO 3166-1 country code (default: 'ro' for Romania)
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
            "Digi24": "https://www.digi24.ro/rss",
            "HotNews": "https://www.hotnews.ro/rss",
            "Mediafax": "https://www.mediafax.ro/rss",
            "ProTV": "https://stirileprotv.ro/rss",
            "Adevarul": "https://adevarul.ro/rss/"
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
            5. Be in Romanian language
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
        
        # First try searching for Romania news
        print("Searching for Romania news...")
        try:
            romania_news = news_api.search_news(query="România", max_results=5)
            if not romania_news.empty:
                print("\nTop news about Romania:")
                for i, (_, article) in enumerate(romania_news.iterrows(), 1):
                    print(f"{i}. {article['title']} ({article['source']})")
                    print(f"   {article['description'][:100]}...")
                    print(f"   URL: {article['url']}")
                    print()
                
                articles_df = romania_news
                top_titles = romania_news["title"].tolist()
            else:
                raise Exception("No results found for Romania search")
                
        except Exception as e:
            print(f"Error searching for Romania news: {e}")
            
            # Try top headlines instead
            print("\nFetching top headlines...")
            headlines = news_api.get_top_headlines(country="ro", max_results=5)
            
            if not headlines.empty:
                print("\nTop 5 news headlines in Romania:")
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
            print("Falling back to predefined Romanian news topics...")
            romanian_topics = [
                "Politică România", 
                "Economie România", 
                "Sport România", 
                "Sănătate România", 
                "Tehnologie România"
            ]
            
            print("\nPredefined Romanian news topics:")
            for i, topic in enumerate(romanian_topics, 1):
                print(f"{i}. {topic}")
            
            top_titles = romanian_topics

    # Print the final list of top titles
    print("\nFinal list of top titles:")
    for i, title in enumerate(top_titles[:5], 1):
        print(f"{i}. {title}")
    
    # Add articles to database
    if not articles_df.empty:
        print("\nAdding articles to database...")
        added_ids = db.add_news_articles(articles_df)
        print(f"Added {len(added_ids)} articles to database")
    
    # Interactive menu for script generation
    try:
        # Use environment variable for API key
        script_generator = ScriptGenerator()
        
        while True:
            print("\n--- SCRIPT GENERATION MENU ---")
            print("1. Generate script for a new article")
            print("2. View recent scripts")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ")
            
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
            
            elif choice == "3":
                print("Exiting script generation menu.")
                break
            
            else:
                print("Invalid choice. Please enter a number between 1 and 3.")
    
    except Exception as e:
        print(f"Error in script generation menu: {e}")
    
    # Close database connection
    db.close()
    print("Program completed.")