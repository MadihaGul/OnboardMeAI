# OnboardMeAI — Repo Chat Helper

Lightweight FastAPI service to ingest a GitHub repo and answer developer questions using RAG.

Quick start

1. Create a virtualenv and install:

```bash
python -m venv .venv
source .venv/bin/activate   # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.

3. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

Usage

- Ingest a repo:

```bash
curl -X POST "http://localhost:8000/ingest" -H "Content-Type: application/json" -d '{"repo_url":"https://github.com/owner/repo"}'
```

- Query the ingested repo:

```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"repo_url":"https://github.com/owner/repo", "question":"Where is the database configuration?"}'
```

Notes & next steps

- FAISS and sentence-transformers may need platform-specific wheels on Windows. If `faiss-cpu` fails to install, consider using Linux or WSL.
- This project is a starting point: you can add richer context extraction (code parsing), caching, auth, or a simple web chat UI.

Frontend

1. Change into the `frontend` folder and install deps:

```bash
cd frontend
npm install
npm run dev
```

2. Open `http://localhost:5173` and use the simple UI to `Ingest` a repo and ask questions.

Git & GitHub

1. Initialize git and push to your GitHub repo (replace URL):

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:youruser/yourrepo.git
git branch -M main
git push -u origin main
```

2. Ensure you do **not** commit secrets like `.env`. `.gitignore` is present to help.
