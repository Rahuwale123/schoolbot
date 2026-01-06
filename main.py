from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import config
import requests
import json
from typing import List, Optional

app = FastAPI(title="School RAG API")

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Model Loading
print(f"Loading model: {config.MODEL_NAME}")
model = SentenceTransformer(config.MODEL_NAME)
client = QdrantClient(url=config.QDRANT_URL)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class SearchResult(BaseModel):
    text: str
    score: float

class WhatsAppRequest(BaseModel):
    phone_number: str
    message: str

@app.post("/query_school", response_model=List[SearchResult])
async def query_school(request: QueryRequest):
    try:
        # 1. Generate Search Vector
        vector = model.encode(request.query).tolist()
        
        # 2. Search Qdrant
        results = client.search(
            collection_name=config.COLLECTION_NAME,
            query_vector=vector,
            limit=request.top_k
        )
        
        # 3. Format Response
        formatted_results = [
            SearchResult(
                text=res.payload.get("text", ""),
                score=res.score
            )
            for res in results
        ]
        
        return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send_whatsapp")
async def send_whatsapp(request: WhatsAppRequest):
    """
    Sends a WhatsApp message using Unipile.
    Directly calls POST /api/v1/chats with multipart/form-data.
    """
    if not config.WHATSAPP_ACCOUNT_ID:
        raise HTTPException(status_code=400, detail="WHATSAPP_ACCOUNT_ID not configured. Run meta.py first.")

    url = f"https://{config.UNIPILE_DSN}/api/v1/chats"
    headers = {
        "X-API-KEY": config.UNIPILE_API_KEY
    }

    try:
        # Clean phone number: remove +, spaces, and any non-numeric characters
        clean_phone = "".join(filter(str.isdigit, request.phone_number))
        
        # Format according to working 'Magic Format'
        attendee_id = f"{clean_phone}@s.whatsapp.net"

        # Must use multipart/form-data for /chats on this instance
        data = [
            ("account_id", config.WHATSAPP_ACCOUNT_ID),
            ("text", request.message),
            ("attendees_ids[]", attendee_id)
        ]

        print(f"--- Sending WhatsApp message to {attendee_id} ---")
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code not in (200, 201):
            print(f"Unipile Chat Error ({response.status_code}): {response.text}")
            
        response.raise_for_status()
        
        return {
            "status": "success",
            "message": "WhatsApp message sent successfully",
            "data": response.json()
        }
        
    except Exception as e:
        print(f"ERROR in send_whatsapp: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(data: dict):
    print(f"--- Received Webhook ---")
    print(json.dumps(data, indent=2))
    return {"status": "received"}

@app.get("/")
async def root():
    return {"message": "School RAG API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
