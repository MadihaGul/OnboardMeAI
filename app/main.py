import os
import hashlib
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from app.ingest import ingest_repo
from app.vectorstore import VectorStore
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATA_DIR = os.getenv('DATA_DIR', './data')
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = OpenAI()

app = FastAPI(title="OnboardMeAI - Repo Chat Helper")

# Allow localhost frontends (Vite:5173, CRA:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
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
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a developer assistant specialized in codebase architecture and implementation details."},
                {"role":"user","content":prompt}
            ],
            max_tokens=600
        )
        # Try multiple access patterns for the response
        try:
            answer = resp['choices'][0]['message']['content']
        except Exception:
            try:
                answer = resp.choices[0].message.content
            except Exception:
                answer = str(resp)
        return {"answer": answer, "sources": [r[0] for r in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")
