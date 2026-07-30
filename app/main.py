import os
import hashlib
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.ingest import ingest_repo
from app.vectorstore import VectorStore
from app.llm import get_llm_provider

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
DATA_DIR = os.getenv('DATA_DIR', './data')

try:
    llm_provider = get_llm_provider()
except ValueError:
    llm_provider = None

app = FastAPI(title="OnboardMeAI - Repo Chat Helper")

# Allow localhost frontends (Vite:5173, Vite:5175, CRA:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None

class QueryRequest(BaseModel):
    repo_url: str
    question: str
    k: Optional[int] = 4

def repo_name_from_url(url: str) -> str:
    h = hashlib.sha1(url.encode()).hexdigest()
    return h

@app.post('/ingest')
def ingest(req: IngestRequest):
    try:
        name = repo_name_from_url(req.repo_url)
        path = ingest_repo(req.repo_url, name, data_dir=DATA_DIR)
        return {"status": "ok", "name": name, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/')
def status():
    return {"status":"ok", "message":"OnboardMeAI running. Use /ingest and /query endpoints or open the frontend."}

@app.post('/query')
def query(req: QueryRequest):
    if llm_provider is None:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY or GEMINI_API_KEY not set")
    name = repo_name_from_url(req.repo_url)
    vs_path = os.path.join(DATA_DIR, name)
    vs = VectorStore(vs_path)
    if not vs.load():
        raise HTTPException(status_code=404, detail="Repository not ingested yet. Call /ingest first")

    raw_results = vs.search(req.question, k=req.k * 4)
    code_results = [item for item in raw_results if item[0].get('type', '').startswith('code') or item[0].get('type') == 'file_role_hint' or item[0].get('type', '').endswith('_summary')]
    doc_results = [item for item in raw_results if item not in code_results]
    results = (code_results + doc_results)[:req.k]

    context_texts = []
    for md, dist in results:
        context_texts.append(
            f"Path: {md.get('path')}\nType: {md.get('type', 'unknown')}\nChunk: {md.get('chunk')}\n---\n{md.get('text','')}\n"
        )

    prompt = (
        "You are a developer assistant specialized in codebase architecture and implementation details. Use only the provided context to answer. "
        "Prioritize implementation source code evidence, code previews, code chunk contents, file role hints, and architecture summaries. "
        "If you need to use README, docs, or config files, explicitly label those references as documentation-based and only use them when direct code evidence is missing. "
        "Do not hallucinate project structure or implementation details beyond what the context supports.\n\n"
        "Context:\n" + "\n".join(context_texts) + "\nQuestion: " + req.question
    )

    try:
        answer = llm_provider.generate_response(prompt)
        return {"answer": answer, "sources": [r[0] for r in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}")
