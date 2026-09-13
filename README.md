# WeatherGPT

A conversational AI weather assistant built for India's linguistic and sectoral diversity. Ask about the weather by voice or text — in English, Hindi, Hinglish, or any of the other languages it supports — and get an answer tailored to what you actually need to know, whether that's a farmer checking soil moisture, a fisherman checking wave height, or a pilot checking visibility.

Built for **Smart India Hackathon 2026**, Problem Statement #68 (Ministry of Earth Sciences).

## What it does

Most weather apps give everyone the same numbers. WeatherGPT instead picks the right lens for the question: a farmer asking about tomorrow's weather gets soil moisture and a spraying recommendation; a fisherman gets wave height and sea safety; a pilot gets visibility and wind gusts; a disaster-risk query gets flood and cyclone warnings; everyone else gets a plain-language everyday forecast. The underlying LLM decides which of these five tools to call based on the question and the user's declared persona — it never invents weather data, only reports what the tools return.

It's reachable two ways: a **Telegram bot** for everyday use, and a **web playground** for testing, demos, and browsing without installing anything.

## How it works

1. **Input** — a voice note or typed message, in whichever language/script the user wrote in, plus a location (shared once via Telegram, or typed/GPS-detected on the web).
2. **Speech-to-text** — Sarvam AI's `saaras:v3` model transcribes voice input, auto-detecting the language and handling code-mixed Hindi/English text naturally.
3. **Reasoning** — Google Gemini (`gemini-3.5-flash-lite`) reads the message together with the user's persona and location, and calls whichever weather tool actually fits the question.
4. **Weather data** — each tool queries the free Open-Meteo API for real conditions (temperature, soil moisture, wave height, visibility, rainfall, etc., depending on the persona) — nothing is fabricated.
5. **Output** — the model replies in the same language and script the user used, in plain conversational sentences rather than a list of numbers. Sarvam's `bulbul:v3` model then speaks the reply aloud (Telegram gets an audio note; the web app plays it inline with a play/pause control).

## Project structure

```
LLM.py                          Core LLM logic: chat sessions, tool registration, persona/location injection
stt.py                          Speech-to-text via Sarvam AI
tts.py                          Text-to-speech via Sarvam AI
WeatherApi.py                   The five persona-specific weather tools, built on Open-Meteo
telebot.py                      Telegram bot: /start, /location, /weather commands
teleToken.py                    Telegram bot token (not committed — see Setup)
server.py                       FastAPI backend for the web app (text + voice endpoints, serves generated audio)
weathergpt.html                 Standalone web frontend: persona picker, live weather widget, voice/text chat
main.py                         Entry point
requirements.txt                Python dependencies
Telegram_input_audio_files/     Incoming voice notes (Telegram + web), created at runtime
Outputs/                        Generated TTS audio files, created at runtime
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set environment variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key
SARVAM_API_KEY=your_sarvam_api_key
```
And a `teleToken.py` for the Telegram bot:
```python
TOKEN = "your_telegram_bot_token"
```

### 3. Run the Telegram bot
```bash
python telebot.py
```
Commands: `/start` for an introduction, `/location` to share your location (required once before asking about weather), `/weather` to get a spoken advisory for your saved location.

### 4. Run the web app
```bash
uvicorn server:app --reload --port 8000
```
Then open `weathergpt.html` in a browser. It talks to the FastAPI server at `localhost:8000` for both text and voice queries, and includes a "Sample bulletin" style live demo as well as a real chat with microphone recording.

## Tech stack

| Layer | Technology |
|---|---|
| LLM & reasoning | Google Gemini (`gemini-3.5-flash-lite`), automatic function calling |
| Speech-to-text | Sarvam AI `saaras:v3` |
| Text-to-speech | Sarvam AI `bulbul:v3` |
| Weather data | Open-Meteo (free, no API key required) |
| Telegram integration | `python-telegram-bot` |
| Web backend | FastAPI |
| Web frontend | Static HTML/CSS/JS with Tailwind, browser `MediaRecorder` for voice capture |

## Supported languages

Hindi, English, Bengali, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu, Gujarati, Assamese, Urdu, Nepali, Konkani, Kashmiri, Sindhi, Sanskrit, Santali, Manipuri, Bodo, Maithili, Dogri, and Roman Hindi/Hinglish — matching Sarvam's supported language set. Quality varies by language; the more widely spoken ones (Hindi, English, and the other major regional languages) are the most reliable.

## Notes

- Weather tool selection is left to the model rather than hardcoded — it reads the persona and the question together, so a farmer asking about flight delays would still get routed to the aviation tool if that's genuinely what they asked.
- The web app's "Talk live" chat and the Telegram bot both go through the same `LLM.py` core, so behavior stays consistent across both surfaces.
- Generated audio files are named uniquely per request so concurrent users don't overwrite each other's output.
