from sarvamai import SarvamAI
from sarvamai.play import save
import os
from uuid import uuid4

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def tts(speech: str, lang: str):
    
    '''
    Args:-
    
    1. speech: The text that is outputted by the LLM.
    2. lang: The language to which you want it to speak, SHould be same as the 'speech'. For eg, hi-IN, ta-IN
    '''
    
    api_key = os.environ.get("SARVAM_API_KEY")
    client = SarvamAI(api_subscription_key=api_key)

    response = client.text_to_speech.convert(
        text= speech,
        language_code= lang,
        model="bulbul:v3",
        speaker="shreya"           # or "meera", "shubh" ,....
    )

    output_path = os.path.join(OUTPUT_DIR, f"response_{uuid4().hex}.wav")
    save(response, output_path)
    return output_path
