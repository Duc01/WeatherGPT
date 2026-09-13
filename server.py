"""
FastAPI wrapper around the existing WeatherGPT backend (LLM.py, stt.py,
tts.py, WeatherApi.py). This file is new — nothing in your existing
backend logic is changed except tts.py (see the note at the top of that
file: it previously had a circular import with LLM.py that would break
the moment both modules were imported together, which this server needs
to do).

Run with:
    pip install fastapi "uvicorn[standard]" python-multipart requests
    uvicorn server:app --reload --port 8000

Then open weathergpt.html in a browser (it's already pointed at
http://localhost:8000).
"""

import os
import re
import uuid

import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from LLM import process_text_message, INPUT_DIR, OUTPUT_DIR
from stt import stt
from tts import tts

app = FastAPI(title="WeatherGPT API")

# Dev-friendly CORS. Once this is deployed somewhere real, replace "*" with
# your actual frontend origin (e.g. "https://weathergpt.yourdomain.com").
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves everything in Outputs/ at http://localhost:8000/audio/<filename>
# so the frontend's <audio> tags can play generated TTS files directly.
app.mount("/audio", StaticFiles(directory=OUTPUT_DIR), name="audio")

PERSONA_LABELS = {
    "farmer": "farmer",
    "fisherman": "fisherman",
    "aviation": "aviation professional",
    "disaster": "disaster management official",
    "public": "general public",
}


def geocode(location: str):
    """
    Turns a place name into (lat, lon, display_name) using Open-Meteo's free
    geocoding API. Also handles the "GPS (lat, lon)" string the frontend
    sends when the user taps the GPS button.
    """
    gps_match = re.match(r"GPS\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", location or "")
    if gps_match:
        lat, lon = float(gps_match.group(1)), float(gps_match.group(2))
        return lat, lon, location

    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("results")
        if results:
            res = results[0]
            return res["latitude"], res["longitude"], res["name"]
    except Exception:
        pass

    # Fallback if geocoding fails or returns nothing: Jaipur, matching the
    # frontend's own default location.
    return 26.9124, 75.7873, location or "Jaipur, Rajasthan"


def detect_lang(text: str) -> str:
    """Devanagari present -> reply in Hindi voice, else English."""
    return "hi-IN" if re.search(r"[\u0900-\u097F]", text) else "en-IN"


class ChatRequest(BaseModel):
    query: str
    persona: str = "public"
    location: str = "Jaipur, Rajasthan"
    session_id: str = "web_default"


def build_response(reply_text: str, persona_label: str, loc_name: str):
    lang = detect_lang(reply_text)
    filename = f"{uuid.uuid4().hex}.wav"
    tts(reply_text, lang=lang, filename=filename)
    return {
        "badge": f"{persona_label.upper()} ADVISORY",
        "metricTag": loc_name,
        "text": reply_text,
        "speechText": reply_text,
        "audioUrl": f"/audio/{filename}",
    }


@app.post("/api/weather-advisory")
def weather_advisory(body: ChatRequest):
    lat, lon, loc_name = geocode(body.location)
    persona_label = PERSONA_LABELS.get(body.persona, "general public")

    # Tell the model explicitly who's asking and where, since the frontend's
    # persona picker and location field are the user's real input, not just
    # keyword matching Gemini has to infer from the raw query.
    augmented_input = (
        f"[User persona: {persona_label}] "
        f"[Location: {loc_name}, latitude={lat}, longitude={lon}] "
        f"{body.query}"
    )

    reply_text = process_text_message(augmented_input, user_id=body.session_id)
    return build_response(reply_text, persona_label, loc_name)


@app.post("/api/voice-advisory")
async def voice_advisory(
    audio: UploadFile = File(...),
    persona: str = Form("public"),
    location: str = Form("Jaipur, Rajasthan"),
    session_id: str = Form("web_default"),
):
    os.makedirs(INPUT_DIR, exist_ok=True)
    in_path = os.path.join(INPUT_DIR, f"{uuid.uuid4().hex}_{audio.filename or 'voice.webm'}")
    with open(in_path, "wb") as f:
        f.write(await audio.read())

    transcript = stt(recording=in_path)

    lat, lon, loc_name = geocode(location)
    persona_label = PERSONA_LABELS.get(persona, "general public")

    augmented_input = (
        f"[User persona: {persona_label}] "
        f"[Location: {loc_name}, latitude={lat}, longitude={lon}] "
        f"{transcript}"
    )
    reply_text = process_text_message(augmented_input, user_id=session_id)

    result = build_response(reply_text, persona_label, loc_name)
    result["transcript"] = transcript
    return result


@app.get("/api/health")
def health():
    return {"status": "ok"}
