# reset_db.py - Quick script to reset the database for testing
import requests

def reset_database():
    print("Resetting database...")
    response = requests.post("http://localhost:5000/api/reset_database")
    if response.status_code == 200:
        print("Success! Database reset.")
        print(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    reset_database() 