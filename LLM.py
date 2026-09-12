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
from WeatherApi import get_farmer_weather
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
        api_key='API KEY HERE'
)
SYSTEM_PROMPT = """
    You are WeatherGPT, an intelligent female weather assistant.

    Rules:
    - Understand English, Hindi, and Roman Hindi/Hinglish.
    - Respond in the same language and script as the user.
    - Never invent weather information.
    - Currently you have no tools
    - For calculations, use the provided analytics tools rather than doing
    unsupported calculations yourself.
"""

user_sessions = {} # Per user Chat session

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
                tools=[get_farmer_weather]
            )
        )
    return user_sessions[user_id]

def get_llm_response(user_input: str, user_id: str) -> str:
    '''
    The Brain of the Project, Just generates the response based on facts gathered.
    '''
    
    chat = get_or_create_chat(user_id)

    start_time = time.perf_counter()
    first_token = True
    full_response = ""

    response = chat.send_message_stream(user_input)
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

def process_voic_mssg(audio_path: str, user_id: str):
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
