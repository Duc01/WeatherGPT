# ==============================================================
#                          IMPORTS
# ==============================================================
from google import genai
from google.genai import types
import os
import time
import soundfile

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

    Rules:
    - Understand English, Hindi, and Roman Hindi/Hinglish.
    - Respond in the same language and script as the user.
    - Never invent weather information — always use the provided weather tools.
    - If the user's message includes a saved location (latitude/longitude),
      use it by default unless the user explicitly names a different place.
    - Choose the most relevant tool based on context: farmer, aviation, disaster risk,
      fisherman, or general weather.
    - For calculations, use the provided analytics tools rather than doing
    unsupported calculations yourself.
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

def get_llm_response(user_input: str, user_id: str) -> str:
    '''
    The Brain of the Project, Just generates the response based on facts gathered.
    '''
    chat = get_or_create_chat(user_id)

    location = get_user_location(user_id)
    if location:
        augmented_input = (
            f"[User's saved location: latitude={location['latitude']}, "
            f"longitude={location['longitude']}] {user_input}"
        )
    else:
        augmented_input = user_input

    start_time = time.perf_counter()
    first_token = True
    full_response = ""

    response = chat.send_message(augmented_input)
    for chunk in response:
        if not chunk.text:
            continue
        if first_token:
            ttft = time.perf_counter() - start_time
            print(f"[TTFT: {ttft:.2f}s]")
            first_token = False
        full_response += chunk.text

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

def process_text_message(user_input: str, user_id: str) -> str:
    """
    Text in -> LLM -> returns response text directly, no TTS.
    """
    return get_llm_response(user_input, user_id)