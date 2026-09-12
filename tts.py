from sarvamai import SarvamAI
from sarvamai.play import save
from LLM import OUTPUT_DIR
import os

def tts(speech: str, lang: str):
    
    '''
    Args:-
    
    1. speech: The text that is outputted by the LLM.
    2. lang: The language to which you want it to speak, SHould be same as the 'speech'. For eg, hi-IN, ta-IN
    '''
    
    client = SarvamAI(api_subscription_key = os.environ["SARVAM_API_KEY"])

    response = client.text_to_speech.convert(
        text= speech,
        language_code= lang,
        model="bulbul:v3",
        speaker="shreya"           # or "meera", "shubh" ,....
    )

    save(response, OUTPUT_DIR)
