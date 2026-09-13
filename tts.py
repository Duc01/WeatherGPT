from sarvamai import SarvamAI
from sarvamai.play import save
import os

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def tts(speech: str, lang: str, filename: str = "response.wav") -> str:
    '''
    Args:
    1. speech: The text that is outputted by the LLM.
    2. lang: The language to speak in, e.g. hi-IN, ta-IN. Should match `speech`.
    3. filename: name of the output .wav file. Pass a unique name per request
       (e.g. a uuid) when multiple users/requests may run concurrently, so
       they don't overwrite each other's audio. Defaults to "response.wav"
       for backward compatibility with existing calls like
       tts(full_response, lang='hi-IN').
 
    Returns:
    Full path to the saved audio file (new — previous version returned None).
    Existing call sites that ignore the return value still work unchanged.
    '''
    client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
 
    response = client.text_to_speech.convert(
        text=speech,
        language_code=lang,
        model="bulbul:v3",
        speaker="shreya"           # or "meera", "shubh", ....
    )
 
    output_path = os.path.join(OUTPUT_DIR, filename)
    save(response, output_path)
    return output_path
