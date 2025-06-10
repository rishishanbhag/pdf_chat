import requests
import json
from chatbot_core import chatbot

def test_chat_endpoint():
    try:
        response = requests.post("http://localhost:8000/chat", 
            json={"question": "What is this document about?", "conversation_id": "123"}
        )
        print("Status Code:", response.status_code)
        print("Response:", json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to FastAPI server. Make sure it's running on port 8000.")
    except Exception as e:
        print(f"Error: {e}")

def test_health_endpoint():
    try:
        response = requests.get("http://localhost:8000/health")
        print("Health Check:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {e}")

def test_direct_chatbot():
    """Test the chatbot core directly (without API)"""
    try:
        print("Testing direct chatbot access...")
        status = chatbot.get_status()
        print("Chatbot status:", json.dumps(status, indent=2))
        
        if status['conversation_chain_initialized']:
            result = chatbot.ask_question("What is this document about?")
            print("Direct chatbot response:", json.dumps(result, indent=2))
        else:
            print("Chatbot not initialized - no documents processed yet")
    except Exception as e:
        print(f"Direct chatbot test failed: {e}")

def test_chatwoot_webhook_validated():
    """Test the new validated Chatwoot webhook endpoint"""
    try:
        payload = {
            "message": "What is this document about?",
            "conversation_id": "test-123",
            "contact": {
                "email": "test@example.com"
            }
        }
        
        response = requests.post("http://localhost:8000/chatwoot-webhook", json=payload)
        print("Chatwoot Webhook Status:", response.status_code)
        print("Chatwoot Response:", json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"Chatwoot webhook test failed: {e}")

if __name__ == "__main__":
    print("Testing FastAPI endpoints...")
    print("\n1. Health Check:")
    test_health_endpoint()
    
    print("\n2. Chat Endpoint:")
    test_chat_endpoint()
    
    print("\n3. Direct Chatbot Test:")
    test_direct_chatbot()

    print("\n4. Chatwoot Webhook Test:")
    test_chatwoot_webhook_validated()