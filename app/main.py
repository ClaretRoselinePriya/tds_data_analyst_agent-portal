# app/main.py
from __future__ import annotations
import io, time, base64
from typing import List

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from PIL import Image

app = FastAPI(title="TDS Minimal Test App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(">>> Loaded minimal app.main. Routes: GET /health, POST /api and /api/")

@app.get("/health")
def health():
    return {"status": "ok", "time": time.time()}

def tiny_png_data_uri() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), (255, 255, 255)).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

@app.post("/api")
@app.post("/api/")
async def api(request: Request):
    form = await request.form()
    uploads: List[UploadFile] = [
        v for _, v in form.multi_items()
        if hasattr(v, "filename") and hasattr(v, "file")
    ]
    if not uploads:
        return JSONResponse(status_code=400, content={"detail": "Missing file upload. Include -F \"questions.txt=@question.txt\""})
    # Always return a valid array quickly
    return JSONResponse(content=[0, 0.0, tiny_png_data_uri()])
