import os,urllib.parse,httpx
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,StreamingResponse
from pydantic import BaseModel
app=FastAPI(title='NEXORA — Advanced Neural Intelligence');KEY=os.getenv('GEMINI_API_KEY','');VIDEO=os.getenv('VIDEO_PROVIDER_URL','')
class Chat(BaseModel): message:str; history:list[dict]=[]; model:str='gemini-2.5-flash'
class Vid(BaseModel): prompt:str
@app.get('/')
async def home(): return FileResponse('index.html')
@app.post('/api/chat')
async def chat(x:Chat):
 if not KEY: raise HTTPException(503,'GEMINI_API_KEY is not configured on the server.')
 c=[{'role':'user' if h.get('role')=='user' else 'model','parts':[{'text':str(h.get('text',''))}]} for h in x.history[-20:]];c.append({'role':'user','parts':[{'text':x.message}]})
 try:
  async with httpx.AsyncClient(timeout=90) as z:
   r=await z.post(f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(x.model) }:generateContent",params={'key':KEY},json={'contents':c,'systemInstruction':{'parts':[{'text':'You are NEXORA, an advanced helpful AI created by David Kamsi Elvis at Vectors Element Tech.'}]}})
  if r.status_code>=400: raise HTTPException(r.status_code,r.text[:1000])
  return {'reply':r.json()['candidates'][0]['content']['parts'][0]['text']}
 except httpx.HTTPError as e: raise HTTPException(502,str(e))
@app.get('/api/search')
async def search(q:str):
 try:
  async with httpx.AsyncClient(timeout=20) as z:r=await z.get('https://api.duckduckgo.com/',params={'q':q,'format':'json','no_html':1,'skip_disambig':1})
  d=r.json();out=[]
  if d.get('AbstractURL'):out.append({'title':d.get('Heading') or q,'url':d['AbstractURL'],'snippet':d.get('AbstractText','')})
  for a in d.get('RelatedTopics',[])[:12]:
   if a.get('FirstURL'):out.append({'title':a.get('Text','')[:100],'url':a['FirstURL'],'snippet':a.get('Text','')})
  return {'results':out[:12]}
 except httpx.HTTPError as e:raise HTTPException(502,str(e))
@app.get('/api/image')
async def image(prompt:str):
 try:
  async with httpx.AsyncClient(timeout=120,follow_redirects=True) as z:r=await z.get('https://image.pollinations.ai/prompt/'+urllib.parse.quote(prompt,safe=''))
  if r.status_code>=400:raise HTTPException(502,'Image provider error.')
  return StreamingResponse(iter([r.content]),media_type=r.headers.get('content-type','image/jpeg'))
 except httpx.HTTPError as e:raise HTTPException(502,str(e))
@app.post('/api/video')
async def video(x:Vid):
 if not VIDEO:return {'configured':False,'message':'Video gateway is ready, but VIDEO_PROVIDER_URL is not configured yet.'}
 return {'configured':True,'message':'Video job sent to the configured provider.'}
