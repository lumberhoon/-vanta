from pathlib import Path
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
import winsound

client = OpenAI()

SAMPLE_RATE = 16_000
CHANNELS = 1

#Globals for current recording session
_current_stream = None
_current_chunks = []

def start_recording():
    """
    Start recording from the default microphone into an in-memory buffer.
    Non-blocking: GUI stays responsive.
    """

    global _current_stream, _current_chunks

    if _current_stream is not None:
        #already recording
        return
    
    _current_chunks = []

    def callback(indata, frames, time, status):
        if status:
            print("[voice] status:", status)
        _current_chunks.append(indata.copy())

    _current_stream = sd.InputStream(
        samplerate = SAMPLE_RATE,
        channels = CHANNELS,
        dtype = "float32",
        callback = callback,
    )
    _current_stream.start()
    print("[voice] recording started")


def _stop_recording_to_file(path: Path):
    """
    Stop the current recording and write it as a WAV to 'path'.
    Returns True if something was recorded, False otherwise.
    """

    global _current_stream, _current_chunks

    if _current_stream is None:
        return False
    
    _current_stream.stop()
    _current_stream.close()
    _current_stream = None
    print("[voice] recording stopped")

    if not _current_chunks:
        return False 
    
    audio = np.concatenate(_current_chunks, axis = 0)
    sf.write(str(path), audio, SAMPLE_RATE)
    return True

def _transcribe_file(path: Path) -> str:
    # Send audio to OpenAI for speech to text
    with path.open("rb") as f:
        result = client.audio.transcriptions.create(
            model = "gpt-4o-mini-transcribe",
            file = f,
        )
    return result.text.strip()

def stop_and_transcribe() -> str:

    """
    High-level helper:
    -stop current recording
    -save to temp WAV
    -send to STT
    -return recognized text (or "")
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "input.wav"
        has_audio = _stop_recording_to_file(wav_path)
        if not has_audio:
            return ""
        text = _transcribe_file(wav_path)
        return text.strip()
    

def play_ptt_ping():

    try:
        winsound.Beep(1200,80)

    except Exception:
        pass


def speak_text(text: str) -> None:
    """
    Use OpenAI TTS to speak the text out load.
    """

    if not text:
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "out.wav"

        resp = client.audio.speech.create(
            model = "gpt-4o-mini-tts",
            voice = "onyx",
            input = text,
        )

        audio_bytes = resp.read()

        with out_path.open("wb") as f:
            f.write(audio_bytes)

        #play it sounddevice
        data, sr = sf.read(str(out_path), dtype = "float32")
        sd.play(data, sr)
        sd.wait()