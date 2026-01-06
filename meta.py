import requests
import json
import time
import qrcode
import os
from PIL import Image
import config

BASE_URL = f"https://{config.UNIPILE_DSN}/api/v1"
HEADERS = {
    "X-API-KEY": config.UNIPILE_API_KEY,
    "Content-Type": "application/json"
}

def login_whatsapp():
    print("--- WhatsApp Login via Unipile ---")
    
    if config.UNIPILE_API_KEY == "your_api_key_here":
        print("ERROR: Please set your UNIPILE_API_KEY in config.py first!")
        return

    # 1. Request new account
    url = f"{BASE_URL}/accounts"
    payload = {
        "type": "messenger",
        "provider": "WHATSAPP"
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code != 200 and response.status_code != 201:
            print(f"Error Response: {response.text}")
        response.raise_for_status()
        data = response.json()
        print(f"Full Response: {json.dumps(data, indent=2)}")
        
        account_id = data.get("account_id")
        qr_code_data = None
        
        checkpoint = data.get("checkpoint")
        if checkpoint and checkpoint.get("type") == "QRCODE":
            qr_code_data = checkpoint.get("qrcode")
        
        print(f"Account ID: {account_id}")
        
        if qr_code_data:
            print("Generating QR Code... Please scan it with your WhatsApp (Linked Devices).")
            # If it's a base64 image or a string for QR
            if qr_code_data.startswith("data:image"):
                # It's a base64 image, we could save it, but better to use a library to show it
                # Unipile usually returns a string that can be encoded as a QR
                pass
            
            # Simple way: Generate a QR image from the string if it's not already an image
            # Or if it's base64, we just save/show it.
            # For now, let's assume it's a string that needs to be QR encoded
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_code_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save("whatsapp_qr.png")
            
            print("\n[SUCCESS] QR Code saved as 'whatsapp_qr.png'. Open it and scan!")
            
            # Wait for connection
            print("\nWaiting for connection status...")
            while True:
                status_url = f"{BASE_URL}/accounts/{account_id}"
                status_res = requests.get(status_url, headers=HEADERS)
                
                if status_res.status_code == 404:
                    print(f"Waiting for account initialization... (404)")
                    time.sleep(5)
                    continue
                
                status_data = status_res.json()
                status = status_data.get("status")
                print(f"Current Status: {status}")
                
                if status == "connected":
                    print("\n✅ WhatsApp connected successfully!")
                    update_config(account_id)
                    break
                elif status == "disconnected":
                    print("\n❌ Login failed or expired. Please try again.")
                    break
                
                time.sleep(5)
        else:
            print("Error: No QR code data received from Unipile.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

def update_config(account_id):
    # Update the config.py file with the new account_id
    with open("config.py", "r") as f:
        lines = f.readlines()
    
    with open("config.py", "w") as f:
        for line in lines:
            if line.startswith("WHATSAPP_ACCOUNT_ID"):
                f.write(f"WHATSAPP_ACCOUNT_ID = \"{account_id}\" \n")
            else:
                f.write(line)
    print(f"Updated config.py with account_id: {account_id}")

if __name__ == "__main__":
    login_whatsapp()
