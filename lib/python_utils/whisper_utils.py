# === WHISPER-BASED TRANSCRIPTION HELPERS ===
# --------------------------------------------------
# These use the OpenAI Whisper model to generate transcriptions.
# Whisper supports better accuracy, especially for noisy audio.
# Requires: pip install openai-whisper
# --------------------------------------------------
#
# Function: whisper_transcribe_full_video(video_path: str) -> str
#   Transcribes the entire video into one block of text using Whisper.
#
# Function: whisper_transcribe_video_by_minute(video_path: str) -> dict[str, str]
#   Breaks the video into 60-second chunks and transcribes each using Whisper.
# --------------------------------------------------


# Initialize the logger
logger = logging.getLogger(__name__)
logger.info(f"📦 {__name__} imported into {__file__}")

def whisper_transcribe_full_video(video_path):
    import whisper
    from moviepy.editor import VideoFileClip
    import tempfile
    import os

    model = whisper.load_model("base")  # You can change to "small", "medium", "large"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        # Extract audio from full video
        clip = VideoFileClip(video_path)
        audio = clip.audio
        audio.write_audiofile(temp_audio_file.name)
        clip.close()

        # Transcribe with Whisper
        result = model.transcribe(temp_audio_file.name)
        os.remove(temp_audio_file.name)
        return result["text"]


def whisper_transcribe_video_by_minute(video_path):
    import whisper
    from moviepy.editor import VideoFileClip
    import tempfile
    import os

    model = whisper.load_model("base")
    video = VideoFileClip(video_path)
    duration = int(video.duration)
    transcript = {}

    for start in range(0, duration, 60):
        end = min(start + 60, duration)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            # Extract 60s audio chunk
            audio_clip = video.audio.subclip(start, end)
            audio_clip.write_audiofile(temp_audio_file.name)

            # Transcribe with Whisper
            result = model.transcribe(temp_audio_file.name)
            os.remove(temp_audio_file.name)
            transcript[f"{start}-{end}s"] = result["text"]

    video.close()
    return transcript






# === FULL VIDEO TRANSCRIPTION ===

def transcribe_full_video(video_path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_path = extract_audio_from_video(video_path, 0, None, temp_audio_file.name)
        transcription = transcribe_audio(audio_path)
        os.remove(audio_path)
        return transcription



def transcribe_video_by_minute(video_path, output_dir):
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

            if text is not None:
                with open(txt_path, "w") as f:
                    f.write(text)
            else:
                with open(txt_path, "w") as f:
                    f.write("[ERROR: No transcript]")
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

