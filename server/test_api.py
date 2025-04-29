# server/test_api.py
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_get_articles():
    print("Testing get_news_articles endpoint...")
    response = requests.get(f"{BASE_URL}/news_articles")
    result = response.json()
    print(f"Status Code: {response.status_code}")
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        articles = result.get("data", {}).get("articles", [])
        if articles:
            return articles[0]["id"]  # Return the ID of the first article
    return None

def test_generate_script(article_id):
    if not article_id:
        print("No article_id available, skipping script generation test")
        return None
        
    print(f"\nTesting generate_script with article_id {article_id}...")
    response = requests.post(
        f"{BASE_URL}/generate_script", 
        json={"article_id": article_id}
    )
    result = response.json()
    print(f"Status Code: {response.status_code}")
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        return result.get("data", {}).get("script_id")
    return None

def test_generate_video_from_article(script_id):
    if not script_id:
        print("No script_id available, skipping video generation test")
        return
        
    print(f"\nTesting generate_video_from_article with script_id {script_id}...")
    response = requests.post(
        f"{BASE_URL}/generate_video_from_article", 
        json={"script_id": script_id}
    )
    result = response.json()
    print(f"Status Code: {response.status_code}")
    print(json.dumps(result, indent=2))

def test_generate_video_from_custom_text():
    print("\nTesting generate_video_from_custom_text...")
    response = requests.post(
        f"{BASE_URL}/generate_video_from_custom_text", 
        json={
            "title": "Test Custom Video", 
            "text": "This is a sample text to test the custom text to video API endpoint. It should generate a short video with narration."
        }
    )
    result = response.json()
    print(f"Status Code: {response.status_code}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("Starting API tests...")
    
    # Test getting articles
    article_id = test_get_articles()
    
    # Test script generation with the article
    if article_id:
        script_id = test_generate_script(article_id)
        
        # Test video generation from article
        if script_id:
            time.sleep(2)  # Give some time for the server to process
            test_generate_video_from_article(script_id)
    
    # Test custom text to video
    test_generate_video_from_custom_text()
    
    print("\nTests completed!")