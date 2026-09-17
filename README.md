# NEXORA — Advanced Neural Intelligence

NEXORA is a futuristic AI workspace by David Kamsi Elvis / Vectors Element Tech.

## Render

Build command:

`pip install -r requirements.txt`

Start command:

`uvicorn server:app --host 0.0.0.0 --port $PORT`

Environment variable:

`GEMINI_API_KEY` = your Gemini API key (keep it in Render, never put it in frontend files).

Optional:

`VIDEO_PROVIDER_URL` = a compatible video gateway URL.

## Important fix in v2

FastAPI now explicitly serves `style.css`, `script.js`, and `manifest.json`. This prevents the common Render problem where `index.html` loads but the CSS/JavaScript files return 404 and the page appears as plain white browser HTML.

Health check: `/health`
