# transcribe_podcast.py — podcast to TTS pipeline 🎙️🧠🔊

import sys
import os
import logging
import requests
import subprocess
import re
from bs4 import BeautifulSoup
from datetime import datetime
print(">>> datetime type:", type(datetime))


# === Load shared utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from utilities1 import (
    initialize_logging,
    load_app_config,
    create_output_directory,
    create_subdir
)

import whisper
from TTS.api import TTS

# === Init logging + config ===
logger = initialize_logging()
config = load_app_config()

# === Podcast Utilities (inline for now) ===

def download_podcast_audio(url: str, output_path="podcast.mp3") -> str:
    try:
        subprocess.run([
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", output_path,
            url
        ], check=True)
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        logger.warning(f"[yt-dlp] Failed: {e}")

    try:
        logger.info("Falling back to scraping for .mp3...")
        res = requests.get(url)
        mp3_links = re.findall(r'https?://[^\"\']+\\.mp3', res.text)
        if not mp3_links:
            raise Exception("No .mp3 found")
        mp3_url = mp3_links[0]

        with requests.get(mp3_url, stream=True) as r:
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return output_path
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise RuntimeError(f"Could not retrieve podcast audio.")

def transcribe_audio_file(audio_path: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

def synthesize_text_to_speech(text: str, output_path: str):
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
    tts.tts_to_file(text=text, file_path=output_path)

# === Main Entry Point ===

if len(sys.argv) < 2:
    print("Usage: python transcribe_podcast.py <podcast_url>")
    sys.exit(1)

podcast_url = sys.argv[1]
logger.info(f"🎧 Processing podcast: {podcast_url}")

try:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = create_output_directory("podcasts")
    run_dir = create_subdir(output_dir, f"run_{timestamp}")

    audio_path = os.path.join(run_dir, "podcast.mp3")
    tts_path = os.path.join(run_dir, "speech.wav")
    transcript_path = os.path.join(run_dir, "transcript.txt")

    # Step 1: Download
    audio_file = download_podcast_audio(podcast_url, audio_path)
    logger.info(f"Audio saved to: {audio_file}")

    # Step 2: Transcribe
    transcript = transcribe_audio_file(audio_file)
    with open(transcript_path, "w") as f:
        f.write(transcript)
    logger.info(f"Transcription written to: {transcript_path}")

    # Step 3: TTS
    synthesize_text_to_speech(transcript, tts_path)
    logger.info(f"Speech audio saved to: {tts_path}")

except Exception as e:
    logger.error(f"💥 Error during podcast processing: {e}")
    sys.exit(1)