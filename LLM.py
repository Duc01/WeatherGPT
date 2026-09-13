# ==============================================================
#                          IMPORTS
# ==============================================================
from google import genai
from google.genai import types
import os
import time
# import soundfile

from dotenv import load_dotenv
load_dotenv()

from stt import stt
from tts import tts
from WeatherApi import get_farmer_weather, get_aviation_weather, get_disaster_risk_weather, get_fisherman_weather, get_general_weather
# ==============================================================
#                          DIRECTORIES
# ==============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "Telegram_input_audio_files") # the audio message recieved from telegram
OUTPUT_DIR = os.path.join(BASE_DIR, "Outputs")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================================
#                          ESSENTIALS
# ==============================================================
client = genai.Client(
        api_key= os.environ["GEMINI_API_KEY"]
)
SYSTEM_PROMPT = """
You are WeatherGPT, an intelligent female weather assistant.

You understand and respond in Hindi, English, Bengali, Kannada, Malayalam,
Marathi, Odia, Punjabi, Tamil, Telugu, Gujarati, Assamese, Urdu, Nepali,
Konkani, Kashmiri, Sindhi, Sanskrit, Santali, Manipuri, Bodo, Maithili,
Dogri, and Roman Hindi/Hinglish — always reply in the same language and
script the user used. Never invent weather information — always use the
provided tools to check real conditions before answering, and pick
whichever tool actually fits the question: farmer, fisherman, aviation,
disaster risk, or general weather. If the user's message includes a
location, use it without asking again unless they mention a different
place.

Write your answers the way you'd explain something to a person standing
next to you, not like a report. A few plain sentences are enough — never
use bullet points, numbered lists, or headers. Don't dump every number the
tool gives you back at the user; pick out only what's relevant to what they
actually asked, and skip the rest. More importantly, don't just state a
fact and stop there — give a short reason behind it, so the person
understands why it matters for what they're about to do. If you tell a
farmer not to spray, say why in one breath, not as a separate point. If
you tell a pilot visibility is dropping, say what that means for their
flight. The goal is that someone reads or hears your answer once and
immediately understands both what's happening and what it means for them,
without having to piece it together themselves.
"""

user_sessions = {} # Per user Chat session

# ==============================================================
#                          LOCATION STORAGE
# ==============================================================
user_locations = {}  # user_id -> {"latitude": ..., "longitude": ...}


def save_user_location(user_id: str, latitude: float, longitude: float):
    """Called once during setup, before the user starts chatting."""
    user_locations[user_id] = {"latitude": latitude, "longitude": longitude}


def get_user_location(user_id: str) -> dict | None:
    return user_locations.get(user_id)


def process_location_setup(latitude: float, longitude: float, user_id: str) -> str:
    """
    Setup step: called when the user shares their location, before
    they start using WeatherGPT. Stores it for all future queries.
    """
    save_user_location(user_id, latitude, longitude)
    return "Location saved! Ab aap mujhse mausam ke baare mein pooch sakte hain."

# ==============================================================
#                          MAIN
# ==============================================================

def get_or_create_chat(user_id: str):
    
    if user_id not in user_sessions:
        user_sessions[user_id] = client.chats.create(
            model="gemini-3.5-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                thinking_config=types.ThinkingConfig(thinking_level='MINIMAL'),
                tools=[get_farmer_weather, get_general_weather, get_fisherman_weather, get_disaster_risk_weather, get_aviation_weather]
            )
        )
    return user_sessions[user_id]

def get_llm_response(user_input: str, user_id: str, location: dict | None = None) -> str:
    '''
    The Brain of the Project, Just generates the response based on facts gathered.
    '''
    chat = get_or_create_chat(user_id)

    location = location or get_user_location(user_id)
    if location:
        augmented_input = (
            f"[User's saved location: latitude={location['latitude']}, "
            f"longitude={location['longitude']}] {user_input}"
        )
    else:
        augmented_input = user_input

    start_time = time.perf_counter()
    response = chat.send_message(augmented_input)
    full_response = response.text
    full_response = response.text or ""
    print(f"[Response time: {time.perf_counter() - start_time:.2f}s]")

    print(f"WeatherGPT ({user_id}): {full_response}")
    return full_response

def process_voice_mssg(audio_path: str, user_id: str):
    """
    Voice in -> transcribe -> LLM -> speak -> returns path to response audio.
    """
    user_input = stt(recording = audio_path)
    full_response = get_llm_response(user_input, user_id)
    
    output_audio_path = tts(full_response, lang='hi-IN')
    
    return output_audio_path

def process_text_message(
    user_input: str, user_id: str, location: dict | None = None
) -> str:
    """
    Text in -> LLM -> returns response text directly, no TTS.
    """
    return get_llm_response(user_input, user_id, location)