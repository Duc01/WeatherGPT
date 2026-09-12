from sarvamai import SarvamAI

def stt(recording  : str) -> str:
    '''
    Args:
    recording- takes the file path of the audio file.
    
    Result:
    Converts speech to text
    '''

    client = SarvamAI(api_subscription_key="Api_key")

    response = client.speech_to_text.transcribe(
            file=open(recording, "rb"),
            model="saaras:v3",
            language_code="unknown",   # specify if known, for better accuracy
            mode="codemix"
        )

    return response.transcript
        