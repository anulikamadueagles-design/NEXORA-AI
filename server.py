import os
import urllib.parse

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

APP_DIR = os.path.dirname(os.path.abspath(__file__))
KEY = os.getenv("GEMINI_API_KEY", "").strip()
VIDEO = os.getenv("VIDEO_PROVIDER_URL", "").strip()

app = FastAPI(title="NEXORA — Advanced Neural Intelligence", version="2.0.0")


class Chat(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    model: str = "gemini-2.5-flash"


class Vid(BaseModel):
    prompt: str


def local_file(name: str) -> str:
    return os.path.join(APP_DIR, name)


# Explicit static-file routes are important on Render/FastAPI. Without these,
# index.html can load while style.css and script.js return 404.
@app.get("/style.css")
async def css():
    return FileResponse(local_file("style.css"), media_type="text/css")


@app.get("/script.js")
async def javascript():
    return FileResponse(local_file("script.js"), media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    return FileResponse(local_file("manifest.json"), media_type="application/manifest+json")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "NEXORA", "version": "2.0.0", "gemini_configured": bool(KEY)}


@app.get("/")
async def home():
    return FileResponse(local_file("index.html"), media_type="text/html")


@app.post("/api/chat")
async def chat(x: Chat):
    if not x.message.strip():
        raise HTTPException(400, "Message cannot be empty.")
    if not KEY:
        raise HTTPException(503, "GEMINI_API_KEY is not configured on the server.")

    contents = []
    for h in x.history[-20:]:
        role = "user" if h.get("role") == "user" else "model"
        text = str(h.get("text", "")).strip()
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": x.message.strip()}]})

    model = x.model.strip() or "gemini-2.5-flash"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model, safe='')}:generateContent"
    )
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are NEXORA, an advanced helpful AI created by David Kamsi Elvis "
                    "at Vectors Element Tech. Be accurate, clear and useful."
                )
            }]
        },
        "generationConfig": {"temperature": 0.7},
    }

    try:
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
            response = await client.post(url, params={"key": KEY}, json=payload)
        if response.status_code >= 400:
            try:
                detail = response.json().get("error", {}).get("message") or response.text
            except Exception:
                detail = response.text
            raise HTTPException(response.status_code, detail[:1200])

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise HTTPException(502, "NEXORA received no response from Gemini.")
        parts = candidates[0].get("content", {}).get("parts", [])
        reply = "\n".join(str(p.get("text", "")) for p in parts if p.get("text"))
        if not reply:
            raise HTTPException(502, "Gemini returned an empty response.")
        return {"reply": reply}
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"AI connection error: {exc}")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected AI error: {exc}")


@app.get("/api/search")
async def search(q: str):
    q = q.strip()
    if not q:
        return {"results": []}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": q, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
        response.raise_for_status()
        data = response.json()
        out = []
        if data.get("AbstractURL"):
            out.append({
                "title": data.get("Heading") or q,
                "url": data["AbstractURL"],
                "snippet": data.get("AbstractText", ""),
            })
        for item in data.get("RelatedTopics", [])[:12]:
            if item.get("FirstURL"):
                out.append({
                    "title": item.get("Text", "")[:100],
                    "url": item["FirstURL"],
                    "snippet": item.get("Text", ""),
                })
        return {"results": out[:12]}
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Search connection error: {exc}")


@app.get("/api/image")
async def image(prompt: str):
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(400, "Image prompt cannot be empty.")
    try:
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt, safe="")
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            response = await client.get(url)
        if response.status_code >= 400:
            raise HTTPException(502, "Image provider error.")
        media_type = response.headers.get("content-type", "image/jpeg")
        return StreamingResponse(iter([response.content]), media_type=media_type)
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Image connection error: {exc}")


@app.post("/api/video")
async def video(x: Vid):
    prompt = x.prompt.strip()
    if not prompt:
        raise HTTPException(400, "Video prompt cannot be empty.")
    if not VIDEO:
        return JSONResponse({
            "configured": False,
            "message": "Video Lab is ready. Add VIDEO_PROVIDER_URL in Render to connect a real video provider.",
        })
    return JSONResponse({
        "configured": True,
        "message": "Video job gateway is connected and ready for the configured provider.",
    })
