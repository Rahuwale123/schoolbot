import requests

URL = "http://localhost:8000/send_whatsapp"
payload = {
    "phone_number": "+919356853041",
    "message": "Final test: WhatsApp RAG Bot is now using the 1-step flow! ✅"
}

try:
    print(f"Sending request to {URL}...")
    response = requests.post(URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
