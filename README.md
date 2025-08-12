# TDS Data Analyst Agent – 2‑Call Planner–Executor (FastAPI)

Single endpoint that accepts `multipart/form-data` with **one required** `questions.txt` (`-F "file=@questions.txt"`) and any number of extra attachments (CSV, Excel, PDF, images, JSON, SQL, Python scripts).

Uses **max 2 LLM calls**:
1) **Planner+Coder** → returns a JSON plan with scrape/ingest steps and ready-to-run code.
2) **Answerer (batched)** → returns a JSON array of answers in original order (2–3 questions per call).

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn app.main:app --reload --port 8000
```
Test:
```bash
curl -F "file=@questions.txt" http://127.0.0.1:8000/
# or with extras
curl -F "file=@questions.txt" -F "file=@data.csv" -F "file=@scan.png" http://127.0.0.1:8000/
```

## Deploy
Build and run the Docker image anywhere:
```bash
docker build -t tds-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY tds-agent
```

## Env vars
```
LLM_PROVIDER=openai|azure|anthropic|local
OPENAI_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=2024-06-01
ANTHROPIC_API_KEY=...
```

## Notes
- Planner/Answerer models configurable in `app/settings.py`.
- Tools cover HTML/PDF/Image/CSV/Excel/JSON/SQL ingestion.
- Plot size enforced < 100 kB for eval compatibility.


---

## Portal Submission Checklist

- [x] Public GitHub repo
- [x] MIT LICENSE present at repo root
- [x] `/health` returns `{"status":"ok"}`
- [x] `/api/` accepts `POST -F "questions.txt=@question.txt"` plus optional additional files
- [x] Returns **pure JSON** in the exact structure requested (array or object)
- [x] Responds within **< 5 minutes** even under 3 parallel requests
- [x] Generates a valid `data:image/png;base64,...` for any plot/image requests under 100kB

### Local quick test

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000

# array output
curl -s -X POST "http://127.0.0.1:8000/api/" -F "questions.txt=@questions.txt"

# simulate 3 parallel portal calls
for i in 1 2 3; do curl -s -X POST "http://127.0.0.1:8000/api/" -F "questions.txt=@questions.txt" & done; wait
```

