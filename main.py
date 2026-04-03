from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
import re
from typing import List, Optional

from ingestion.document_loader import DocumentLoader
from ingestion.chunking import SemanticChunker
from retrieval.vector_store import VectorStore
from graph.knowledge_graph import KnowledgeGraph
from cache.cache_manager import SemanticCache
from routing.query_router import QueryRouter
from utils.llm_interface import LLMInterface
from utils.evaluation import EvaluationMetrics

app = FastAPI(title="FinVault-X API", description="Adaptive Hybrid CAG-RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data", exist_ok=True)
os.makedirs("ui", exist_ok=True)

# Global modules (initialized lazily or in startup)
doc_loader = DocumentLoader()
chunker = SemanticChunker()
vector_store = None
kg = None
cache = None
router = None
llm = LLMInterface()
eval_metrics = EvaluationMetrics()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    route_used: str
    context: str
    latency_sec: float
    execution_steps: List[str] = []
    matched_query: Optional[str] = None
    suggestions: List[str] = []

async def perform_ingestion():
    """Shared logic for loading and indexing documents"""
    if not vector_store or not kg:
        return 0, 0
        
    raw_docs = doc_loader.load_documents()
    if not raw_docs:
        print("💡 Auto-Load: No documents found in 'data/' folder.")
        return 0, 0
        
    chunks = chunker.chunk_documents(raw_docs)
    vector_store.add_documents(chunks)
    kg.build_from_documents(chunks)
    
    # Reset cache
    if cache:
        cache.cache = {}
        cache.hits = 0
        cache.misses = 0
    return len(raw_docs), len(chunks)

async def initialize_system():
    global vector_store, kg, cache, router
    try:
        print("📥 Model Loading: Initializing SentenceTransformer and spaCy...")
        vector_store = VectorStore()
        kg = KnowledgeGraph()
        cache = SemanticCache()
        router = QueryRouter()
        
        print("📥 Auto-Load: Scanning 'data/' folder...")
        docs, chunks = await perform_ingestion()
        if docs > 0:
            print(f"✅ Auto-Load Success: Ingested {docs} docs and {chunks} chunks.")
        print("✅ System Ready: Models loaded and documents indexed.")
    except Exception as e:
        print(f"⚠️ Initialization Failed: {e}")

@app.on_event("startup")
async def startup_event():
    """Start the server immediately and run ingestion/model loading in the background"""
    print("🚀 Project Starting: Server is opening on port 8000...")
    # Initialize heavy models in the background so the port opens instantly
    asyncio.create_task(initialize_system())

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("ui/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    for file in files:
        with open(os.path.join("data", file.filename), "wb") as f:
            f.write(await file.read())
    return {"message": "Files saved locally in `./data/`!"}

@app.post("/ingest")
async def ingest_documents():
    """Manual trigger to re-ingest docs"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="System is still initializing models. Please wait.")
    try:
        docs, chunks = await perform_ingestion()
        if docs == 0:
            return {"message": "No documents found in data folder."}
        return {"message": f"Ingested {docs} docs -> {chunks} semantic chunks. Vector DB & Knowledge Graph updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(req: QueryRequest):
    if not vector_store or not router:
         raise HTTPException(status_code=503, detail="System is still initializing models. Please wait.")
         
    eval_metrics.start_timer()
    query = req.query
    
    # 2. Semantic Cache (CAG)
    cached_response, matched_query = cache.get(query)
    if cached_response:
        latency = eval_metrics.end_timer()
        execution_steps = [
            "Cache - found here",
            "Vector DB - Not reached",
            "RAG - Not reached",
            "Local LLM - Not reached"
        ]
        return QueryResponse(
            response=cached_response,
            route_used="CACHE (CAG)",
            context="[Retrieved from Semantic Cache]",
            latency_sec=latency,
            execution_steps=execution_steps,
            matched_query=matched_query,
            suggestions=["Tell me more about this.", "How does this relate to previous data?", "Can you provide a summary?"]
        )
        
    # 1. Adaptive Routing (Determine intent first)
    route = router.route(query)
    
    status_cache = "Not Found"
    status_vector = "Not reached"
    status_rag = "Not reached"
    status_llm = "reached" # LLM is always reached if Cache is missed
    
    context = ""
    route_desc = ""
    # 3. Retrieval
    if route == "graph":
        context = kg.search(query)
        if not context: 
            status_rag = "Not Found"
            route_desc = "vector (fallback from graph)"
            status_vector = "found here"
            docs = vector_store.search(query)
            context = "\n\n".join([d["content"] for d in docs])
        else:
            status_rag = "found here"
            route_desc = "graph"
    else:
        # Standard Vector RAG
        status_vector = "found here"
        route_desc = "vector"
        docs = vector_store.search(query)
        context = "\n\n".join([d["content"] for d in docs])
        
    execution_steps = [
        f"Cache - {status_cache}",
        f"Vector DB - {status_vector}",
        f"RAG - {status_rag}",
        f"Local LLM - {status_llm}"
    ]
    
    # 4. LLM Generation
    system_prompt = (
        "You are an AI Banking Assistant for FinVault-X. "
        "Use the provided context to answer the query accurately. "
        "Your response must be around 100 words in length. "
        "At the very end, strictly include 3 follow-up questions formatted as: "
        "Suggestions: [Question 1] | [Question 2] | [Question 3]"
    )
    
    full_response = llm.generate_response(query, context, system_prompt)
    
    # Extract suggestions from response
    cleaned_response = full_response
    suggestions = ["Summarize this answer.", "Give more details.", "What are the risks?"] # Fallback
    
    if "suggestions:" in full_response.lower():
        # Split at several possible sentinel points
        sentinel_split = re.split(r"suggestions:", full_response, flags=re.IGNORECASE)
        cleaned_response = sentinel_split[0].strip()
        if len(sentinel_split) > 1:
            raw_sugg = sentinel_split[1].strip()
            # Split by: Pipes (|), Newlines with bullets, OR question marks followed by space
            # This is the most robust way to capture Q1? Q2? Q3? format too.
            raw_list = re.split(r"\||\r?\n\s*[-*•\d\.\]\)\[]*\s*|\?\s+(?=[A-Z])", raw_sugg)
            # Filter and clean up (trimming special chars)
            suggestions = [s.strip(" []?|.*•-") for s in raw_list if len(s.strip()) > 3]
            # Add back the question mark manually if it was stripped at the end
            suggestions = [s + "?" if not s.endswith("?") else s for s in suggestions]

    latency = eval_metrics.end_timer()
    return QueryResponse(
        response=cleaned_response,
        route_used=route_desc,
        context=context or "No specific context found.",
        latency_sec=latency,
        execution_steps=execution_steps,
        suggestions=suggestions[:3],
        matched_query=None
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
