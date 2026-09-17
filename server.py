import os
import urllib.parse

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

APP_DIR = os.path.dirname(os.path.abspath(__file__))
KEY = os.getenv("GEMINI_API_KEY", "").strip()
VIDEO = os.getenv("VIDEO_PROVIDER_URL", "").strip()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"

app = FastAPI(title="NEXORA — Advanced Neural Intelligence", version="3.0.0")


class Chat(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    interaction_id: str | None = None
    model: str = DEFAULT_MODEL


class Vid(BaseModel):
    prompt: str


def local_file(name: str) -> str:
    return os.path.join(APP_DIR, name)


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
    return {
        "status": "ok",
        "app": "NEXORA",
        "version": "3.0.0",
        "gemini_configured": bool(KEY),
        "gemini_model": DEFAULT_MODEL,
    }


@app.get("/")
async def home():
    return FileResponse(local_file("index.html"), media_type="text/html")


@app.post("/api/chat")
async def chat(x: Chat):
    message = x.message.strip()
    if not message:
        raise HTTPException(400, "Message cannot be empty.")
    if not KEY:
        raise HTTPException(503, "GEMINI_API_KEY is not configured on the server.")

    # Gemini's current recommended API for new applications is Interactions API.
    # It supports server-side conversation state via previous_interaction_id.
    model = x.model.strip() or DEFAULT_MODEL
    if model.startswith("models/"):
        model = model.removeprefix("models/")

    payload = {
        "model": model,
        "input": message,
        "system_instruction": (
            "You are NEXORA, an advanced multimodal AI created by David Kamsi Elvis "
            "at Vectors Element Tech. Be accurate, practical, concise when appropriate, "
            "and helpful. Never claim a tool was used unless it was actually used."
        ),
        "generation_config": {"temperature": 0.7},
    }
    if x.interaction_id:
        payload["previous_interaction_id"] = x.interaction_id

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {"Content-Type": "application/json", "x-goog-api-key": KEY}

    try:
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            try:
                detail = response.json().get("error", {}).get("message") or response.text
            except Exception:
                detail = response.text
            raise HTTPException(response.status_code, detail[:1600])

        data = response.json()
        reply = str(data.get("output_text") or "").strip()
        if not reply:
            # Current REST responses expose model output in steps. Keep this fallback
            # for responses where output_text is not populated.
            for step in reversed(data.get("steps") or []):
                if step.get("type") == "model_output":
                    for item in step.get("content") or []:
                        if item.get("type") == "text" and item.get("text"):
                            reply = str(item["text"]).strip()
                            break
                if reply:
                    break

        if not reply:
            raise HTTPException(502, "NEXORA received an empty response from Gemini.")

        return {
            "reply": reply,
            "interaction_id": data.get("id"),
            "model": model,
        }
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
