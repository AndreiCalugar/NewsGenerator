# server/test_api.py
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_generate_script():
    print("Testing generate_script endpoint...")
    response = requests.post(f"{BASE_URL}/generate_script")
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
    
    # Test script generation
    script_id = test_generate_script()
    
    # Allow some time for the server to process
    if script_id:
        print("Waiting 2 seconds before testing video generation...")
        time.sleep(2)
        
        # Test video generation from article
        test_generate_video_from_article(script_id)
    
    # Test custom text to video
    test_generate_video_from_custom_text()
    
    print("\nTests completed!")