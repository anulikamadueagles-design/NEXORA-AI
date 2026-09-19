import os,httpx
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.parse import quote
app=FastAPI(title="NEXORA");ROOT=os.path.dirname(os.path.abspath(__file__))
class Chat(BaseModel): message:str
@app.get("/")
async def home(): return FileResponse(os.path.join(ROOT,"index.html"))
@app.get("/style.css")
async def css(): return FileResponse(os.path.join(ROOT,"style.css"),media_type="text/css")
@app.get("/script.js")
async def js(): return FileResponse(os.path.join(ROOT,"script.js"),media_type="application/javascript")
@app.get("/health")
async def health(): return {"status":"ok","app":"NEXORA"}
@app.post("/api/chat")
async def chat(x:Chat):
 k=os.getenv("GEMINI_API_KEY","").strip()
 if not k: raise HTTPException(503,"GEMINI_API_KEY is not configured.")
 async with httpx.AsyncClient(timeout=60) as c:r=await c.post("https://generativelanguage.googleapis.com/v1beta/interactions",headers={"x-goog-api-key":k,"Content-Type":"application/json"},json={"model":os.getenv("GEMINI_MODEL","gemini-3.6-flash"),"input":x.message})
 if r.status_code>=400: raise HTTPException(r.status_code,r.text[:500])
 d=r.json();o=d.get("outputs") or [];return {"text":o[-1].get("text","") if o else ""}
@app.get("/api/search")
async def search(q:str):
 async with httpx.AsyncClient(timeout=20,headers={"User-Agent":"NEXORA/1.0"}) as c:r=await c.get("https://api.duckduckgo.com/",params={"q":q,"format":"json","no_html":1})
 d=r.json();a=[]
 if d.get("AbstractText"):a.append({"title":d.get("Heading","Result"),"url":d.get("AbstractURL",""),"snippet":d["AbstractText"]})
 for x in d.get("RelatedTopics",[])[:8]:
  if isinstance(x,dict) and x.get("Text"):a.append({"title":x["Text"][:100],"url":x.get("FirstURL",""),"snippet":x["Text"]})
 return {"results":a}
@app.get("/api/image")
async def image(prompt:str):return {"url":"https://image.pollinations.ai/prompt/"+quote(prompt)+"?width=1024&height=1024&nologo=true"}
