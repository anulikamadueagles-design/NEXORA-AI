# NEXORA — Advanced Neural Intelligence

Created by **David Kamsi Elvis** · **Vectors Element Tech**

## GitHub + Render deployment

1. Upload **all files directly into the root of your existing GitHub repository**.
2. Do not put them inside another folder.
3. Commit to the `main` branch.
4. Your existing Render Web Service should redeploy automatically.
5. In Render → Environment, add:
   - `GEMINI_API_KEY` = your Gemini API key
   - Optional: `VIDEO_PROVIDER_URL` for a compatible video-generation gateway.
6. Render build command:
   `pip install -r requirements.txt`
7. Render start command:
   `uvicorn server:app --host 0.0.0.0 --port $PORT`

The frontend uses cache-busting query versions (`?v=nexora4`) so the new design is easier to distinguish from an older deployment.

This release is a strong full-stack foundation. Real authentication, persistent cloud memory/database, production file storage, distributed video rendering, collaboration, payments and provider-specific AI pipelines still require their respective services/credentials.
