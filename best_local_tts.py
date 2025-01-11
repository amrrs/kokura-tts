from models import build_model
import torch
import soundfile as sf
from kokoro import generate

SAMPLE_RATE = 24000
OUTPUT_FILE = "output.wav"

TEXT = """
Hey please subscribe to 1Littlecoder! He is amazing!
"""

device = "cuda" if torch.cuda.is_available() else "cpu" #mps

print(f"Runnin on device: {device}")

MODEL = build_model("kokoro-v0_19.pth", device)

VOICE_NAME = "af_sky"

VOICEPACK = torch.load(f"voices/{VOICE_NAME}.pt", weights_only=True).to(device)

print(f"Loaded voice: {VOICE_NAME}")

audio = []
for chunk in TEXT.split("."):
    print(chunk)
    if len(chunk) < 2:
        # a try except block for non verbalizable text is probably better than this hack
        continue
    snippet, _ = generate(MODEL, chunk, VOICEPACK, lang=VOICE_NAME[0])
    audio.extend(snippet)

sf.write(OUTPUT_FILE, audio, SAMPLE_RATE)
