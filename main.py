from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from typing import List

app = FastAPI(title="School RAG API")

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "school_info"
MODEL_NAME = "all-MiniLM-L6-v2"

# Global Model Loading
print(f"Loading model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(url=QDRANT_URL)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class SearchResult(BaseModel):
    text: str
    score: float

@app.post("/query_school", response_model=List[SearchResult])
async def query_school(request: QueryRequest):
    try:
        # 1. Generate Search Vector
        vector = model.encode(request.query).tolist()
        
        # 2. Search Qdrant
        results = client.search(
            collection_name=COLLECTION_NAME,
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

@app.get("/")
async def root():
    return {"message": "School RAG API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
