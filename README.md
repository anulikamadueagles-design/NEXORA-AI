# NEXORA — Advanced Neural Intelligence

NEXORA is a responsive sci-fi AI workspace by David Kamsi Elvis / Vectors Element Tech.

## Important Render variables

- `GEMINI_API_KEY` — your Gemini API key
- `GEMINI_MODEL` — defaults to `gemini-3.6-flash`
- `VIDEO_PROVIDER_URL` — optional video provider gateway

The chat backend uses Google's current Interactions API and server-side `previous_interaction_id` conversation state.

## Render

Build: `pip install -r requirements.txt`

Start: `uvicorn server:app --host 0.0.0.0 --port $PORT`

Health: `/health`
