# === WHISPER-BASED TRANSCRIPTION HELPERS ===
# --------------------------------------------------
# These use the OpenAI Whisper model to generate transcriptions.
# Whisper supports better accuracy, especially for noisy audio.
# Requires: pip install openai-whisper, moviepy, SpeechRecognition
# --------------------------------------------------
#
# Function: whisper_transcribe_full_video(video_path: str) -> str
#   Transcribes the entire video into one block of text using Whisper.
#
# Function: whisper_transcribe_video_by_minute(video_path: str) -> dict[str, str]
#   Breaks the video into 60-second chunks and transcribes each using Whisper.
# --------------------------------------------------

import os
import tempfile
import logging
import time

from moviepy.editor import VideoFileClip
import whisper
import speech_recognition as sr

# === Logger Setup ===
logger = logging.getLogger(__name__)
logger.info(f"📦 {__name__} imported into {__file__}")

# === WHISPER TRANSCRIPTION FUNCTIONS ===

def whisper_transcribe_full_video(video_path):
    """
    Transcribes an entire video using OpenAI's Whisper model.

    Args:
        video_path (str): Path to input video.

    Returns:
        str: Full transcription as one block of text.
    """
    model = whisper.load_model("base")  # Options: tiny, base, small, medium, large

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        clip = VideoFileClip(video_path)
        audio = clip.audio
        audio.write_audiofile(temp_audio_file.name)
        clip.close()

        result = model.transcribe(temp_audio_file.name)
        os.remove(temp_audio_file.name)
        return result["text"]


def whisper_transcribe_video_by_minute(video_path):
    """
    Breaks a video into 60-second chunks and transcribes each using Whisper.

    Args:
        video_path (str): Path to input video.

    Returns:
        dict[str, str]: Mapping of time ranges to transcribed text.
    """
    model = whisper.load_model("base")
    video = VideoFileClip(video_path)
    duration = int(video.duration)
    transcript = {}

    for start in range(0, duration, 60):
        end = min(start + 60, duration)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio_clip = video.audio.subclip(start, end)
            audio_clip.write_audiofile(temp_audio_file.name)

            result = model.transcribe(temp_audio_file.name)
            os.remove(temp_audio_file.name)
            transcript[f"{start}-{end}s"] = result["text"]

    video.close()
    return transcript

# === GOOGLE SPEECH RECOGNITION TRANSCRIPTION ===

def transcribe_full_video(video_path):
    """
    Transcribes a full video using Google Speech Recognition (fallback method).

    Args:
        video_path (str): Path to input video.

    Returns:
        str: Full transcription.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_path = extract_audio_from_video(video_path, 0, None, temp_audio_file.name)
        transcription = transcribe_audio(audio_path)
        os.remove(audio_path)
        return transcription


def transcribe_video_by_minute(video_path, output_dir):
    """
    Transcribes video in 1-minute chunks using Google Speech Recognition.
    Useful as a fallback when Whisper isn't ideal.

    Args:
        video_path (str): Path to input video.
        output_dir (str): Directory to store audio/text files.

    Returns:
        str: Full stitched transcript.
    """
    video = VideoFileClip(video_path)
    duration = int(video.duration)
    os.makedirs(output_dir, exist_ok=True)
    recognizer = sr.Recognizer()
    stitched_transcript = []

    for start in range(0, duration, 60):
        end = min(start + 60, duration)
        base_name = f"min_{start // 60:02d}"
        wav_path = os.path.join(output_dir, f"{base_name}.wav")
        txt_path = os.path.join(output_dir, f"{base_name}.txt")

        if not os.path.exists(wav_path):
            try:
                logger.info(f"🎧 Exporting audio {start}-{end} sec → {wav_path}")
                audio_clip = video.audio.subclip(start, end)
                audio_clip.write_audiofile(wav_path)
            except Exception as e:
                logger.error(f"❌ Failed to export audio: {e}")
                continue

        if not os.path.exists(txt_path):
            logger.info(f"🗣️ Transcribing {base_name}.wav...")
            text = None
            for attempt in range(3):
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data)
                    break
                except sr.UnknownValueError:
                    text = "[Unintelligible]"
                    break
                except sr.RequestError as e:
                    logger.warning(f"⚠️ Google error on attempt {attempt+1}: {e}")
                    time.sleep(2**attempt)
                    text = None

            with open(txt_path, "w") as f:
                f.write(text if text is not None else "[ERROR: No transcript]")
        else:
            with open(txt_path, "r") as f:
                text = f.read()

        stitched_transcript.append(f"[{start}-{end} sec]\n{text}\n")

    final_path = os.path.join(output_dir, "full_transcript.txt")
    with open(final_path, "w") as f:
        f.write("\n".join(stitched_transcript))

    logger.info(f"✅ Full transcript saved to: {final_path}")
    return "\n".join(stitched_transcript)


import requests
from bs4 import BeautifulSoup
import re

def extract_editorial_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.extract()

    main_content = (
        soup.find("article") or 
        soup.find("div", {"id": "main-content"}) or 
        soup.find("div", {"class": "content"})
    )

    if main_content:
        return main_content

    paragraphs = soup.find_all("p")
    wrapper = soup.new_tag("div")
    for p in paragraphs[:200]:
        wrapper.append(p)
    return wrapper

def get_text_with_italics(element):
    parts = []
    for tag in element.descendants:
        if tag.name in ["em", "i"]:
            parts.append(f"*{tag.get_text(strip=True)}*")
        elif tag.name is None:
            parts.append(tag.strip())
    return " ".join(parts)

def slugify_url(url):
    return re.sub(r'\W+', '-', url.split("//")[-1].split("/")[0].replace("www.", "")).strip("-")

def distill_run_snapshot(output_dir, input_video, urls, config):
    import socket
    import getpass
    import platform
    import subprocess
    import traceback

    tb_dir = os.path.join(output_dir, "tb")
    os.makedirs(tb_dir, exist_ok=True)
    logger.info(f"Creating snapshot in: {tb_dir}")

    # === Basic metadata ===
    try:
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "input_video": input_video,
            "urls_scraped": urls,
            "user": getpass.getuser(),
            "hostname": socket.gethostname(),
            "platform": platform.platform()
        }
        meta_path = os.path.join(tb_dir, "snapshot.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Wrote metadata snapshot: {meta_path}")
    except Exception as e:
        logger.warning("❌ Failed to write snapshot.json")
        logger.debug(traceback.format_exc())

    # === Dump app config ===
    try:
        config_app_path = os.path.join(tb_dir, "config_app.json")
        with open(config_app_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Wrote app config: {config_app_path}")
    except Exception:
        logger.warning("❌ Could not dump config_app.json")
        logger.debug(traceback.format_exc())

    # === Copy platform config ===
    try:
        platform_config_path = os.path.join(current_dir, "../conf/config.json")
        if os.path.exists(platform_config_path):
            with open(platform_config_path, "r") as f:
                platform_config = json.load(f)
            platform_out_path = os.path.join(tb_dir, "config_platform.json")
            with open(platform_out_path, "w") as f:
                json.dump(platform_config, f, indent=2)
            logger.info(f"Copied platform config to: {platform_out_path}")
        else:
            logger.info(f"No platform config found at {platform_config_path}")
    except Exception:
        logger.warning("❌ Could not copy platform config")
        logger.debug(traceback.format_exc())

    # === Save pip freeze ===
    try:
        result = subprocess.run(["pip", "freeze"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        env_path = os.path.join(tb_dir, "env.txt")
        with open(env_path, "w") as f:
            f.write(result.stdout)
        logger.info(f"Saved environment snapshot to: {env_path}")
    except Exception:
        logger.warning("❌ Could not generate pip freeze")
        logger.debug(traceback.format_exc())

    logger.info(f"📦 Snapshot completed and saved in: {tb_dir}")

import re

def chunk_sentences(audio_path, model_name='base'):
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, verbose=False)

    segments = result['segments']  # contains timestamps and text
    all_text = ""
    time_cursor = 0.0
    chunks = []
    
    for seg in segments:
        all_text += seg['text'].strip() + " "

    # Split by sentence
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, all_text.strip())

    seg_idx = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        start_time = None
        end_time = None

        # Get approximate start and end from segments
        acc_text = ""
        while seg_idx < len(segments) and len(acc_text) < len(sentence):
            seg = segments[seg_idx]
            if start_time is None:
                start_time = seg['start']
            end_time = seg['end']
            acc_text += seg['text'].strip() + " "
            seg_idx += 1

        chunks.append({
            "text": sentence,
            "start": round(start_time, 2) if start_time else None,
            "end": round(end_time, 2) if end_time else None
        })

    # Output path
    out_path = os.path.splitext(audio_path)[0] + "_sentences.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print(f"Saved sentence chunks to {out_path}")
    return out_path


def write_srt(segments, output_path):
    def format_timestamp(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            text = seg['text'].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    print(f"🎬 SRT saved to {output_path}")
    
def write_vtt(segments, output_path):
    def format_timestamp(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            text = seg['text'].strip()
            f.write(f"{start} --> {end}\n{text}\n\n")
    print(f"🌍 VTT saved to {output_path}")



