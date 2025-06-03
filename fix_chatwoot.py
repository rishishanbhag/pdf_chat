import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

# Get credentials from environment
CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN")
CHATWOOT_BOT_TOKEN = os.getenv("CHATWOOT_BOT_TOKEN")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")
CHATWOOT_URL = os.getenv("CHATWOOT_URL", "https://app.chatwoot.com")

def send_reply_to_chatwoot(conversation_id, message):
    """Send a reply back to Chatwoot conversation"""
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    
    # First try with API token
    headers = {
        "Content-Type": "application/json",
        "api_access_token": CHATWOOT_API_TOKEN
    }
    
    payload = {
        "content": message,
        "message_type": "outgoing"
    }
    
    print(f"Sending reply to conversation {conversation_id}")
    print(f"URL: {url}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    # If first attempt fails, try with bot token
    if response.status_code != 200:
        print(f"First attempt failed with API token: {response.status_code}")
        print(f"Trying with BOT token...")
        
        headers = {
            "Content-Type": "application/json",
            "api_access_token": CHATWOOT_BOT_TOKEN
        }
        
        response = requests.post(url, headers=headers, json=payload)
    
    # Report results
    if response.status_code == 200:
        print("✅ Reply sent successfully!")
        print(f"Response: {response.text}")
        return True
    else:
        print(f"❌ Failed to send reply: {response.status_code}")
        print(f"Response: {response.text}")
        return False

# Test function
if __name__ == "__main__":
    conversation_id = 1  # Use your conversation ID
    test_message = "Hello! This is a test reply from the PDF bot."
    send_reply_to_chatwoot(conversation_id, test_message)