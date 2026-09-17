import os, urllib.parse
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app=FastAPI(title="NEXORA Advanced Neural Intelligence")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")
VIDEO_PROVIDER_URL=os.getenv("VIDEO_PROVIDER_URL","")

class ChatRequest(BaseModel):
    message:str
    history:list[dict]=[]
    model:str="gemini-2.5-flash"

class VideoRequest(BaseModel):
    prompt:str

@app.get("/")
async def home(): return FileResponse("index.html")

@app.post("/api/chat")
async def chat(req:ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(503,"GEMINI_API_KEY is not configured on the server.")
    contents=[]
    for h in req.history[-20:]:
        role="user" if h.get("role")=="user" else "model"
        contents.append({"role":role,"parts":[{"text":str(h.get("text",""))}]})
    contents.append({"role":"user","parts":[{"text":req.message}]})
    model=req.model or "gemini-2.5-flash"
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r=await client.post(url,params={"key":GEMINI_API_KEY},json={"contents":contents,"systemInstruction":{"parts":[{"text":"You are NEXORA, an advanced, helpful multimodal AI created by David Kamsi Elvis at Vectors Element Tech. Be accurate, concise and useful."}]}})
        if r.status_code>=400: raise HTTPException(r.status_code, r.text[:1000])
        data=r.json()
        reply=data["candidates"][0]["content"]["parts"][0]["text"]
        return {"reply":reply}
    except httpx.HTTPError as e: raise HTTPException(502,str(e))

@app.get("/api/search")
async def search(q:str):
    if not q.strip(): return {"results":[]}
    url="https://api.duckduckgo.com/"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.get(url,params={"q":q,"format":"json","no_html":1,"skip_disambig":1})
        data=r.json(); results=[]
        if data.get("AbstractURL"):
            results.append({"title":data.get("Heading") or q,"url":data["AbstractURL"],"snippet":data.get("AbstractText","")})
        for item in data.get("RelatedTopics",[])[:10]:
            if "FirstURL" in item:
                results.append({"title":item.get("Text","")[:100],"url":item["FirstURL"],"snippet":item.get("Text","")})
            elif item.get("Topics"):
                for sub in item["Topics"][:3]:
                    if "FirstURL" in sub: results.append({"title":sub.get("Text","")[:100],"url":sub["FirstURL"],"snippet":sub.get("Text","")})
        return {"results":results[:12]}
    except httpx.HTTPError as e: raise HTTPException(502,str(e))

@app.get("/api/image")
async def image(prompt:str):
    # Pollinations provides a simple public image-generation URL.
    encoded=urllib.parse.quote(prompt,safe="")
    target=f"https://image.pollinations.ai/prompt/{encoded}"
    try:
        client=httpx.AsyncClient(timeout=120,follow_redirects=True)
        r=await client.get(target)
        if r.status_code>=400: raise HTTPException(502,"Image provider returned an error.")
        media=r.headers.get("content-type","image/jpeg")
        return StreamingResponse(iter([r.content]),media_type=media)
    except httpx.HTTPError as e: raise HTTPException(502,str(e))

@app.post("/api/video")
async def video(req:VideoRequest):
    if not VIDEO_PROVIDER_URL:
        return {"configured":False,"message":"Video generation gateway is ready, but VIDEO_PROVIDER_URL is not configured yet."}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r=await client.post(VIDEO_PROVIDER_URL,json={"prompt":req.prompt})
        return {"configured":True,"status":r.status_code,"message":"Video job sent to the configured provider."}
    except httpx.HTTPError as e: raise HTTPException(502,str(e))

app.mount("/static",StaticFiles(directory="."),name="static")
