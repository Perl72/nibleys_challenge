# ==================================================
# utilities2.py - Video Processing Utility
# ==================================================
#
# Function List:
# 1. initialize_logging() -> logging.Logger
#    Initializes logging for the script.
#
# 2. extract_audio_from_video(video_path: str, start_time: float, end_time: float, temp_audio_path: str) -> str
#    Extracts audio from a video between the specified time range.
#
# 3. transcribe_audio(audio_path: str) -> str
#    Converts an audio file to text using speech recognition.
#
# 4. process_clip(video_path: str, start_time: float, end_time: float) -> str
#    Extracts, transcribes, and allows confirmation of the text before adding captions.
#
# 5. process_clips_moviepy(config: dict, clips: dict, logger: logging.Logger, input_video: str, output_dir: str, captions_config)
#    Processes video clips by adding captions and saving them.
#
# 6. create_output_directory(base_dir: str = "clips") -> str
#    Creates an output directory named based on a timestamp and video filename.
#
# 7. load_clips_from_file(file_path: str) -> dict
#    Loads clips data from a JSON or YAML file.
#
# 8. stitch_clips(clip_files: list, output_file: str)
#    Stitches multiple video clips into one output file.
#
# 9. generate_clip_transcripts(input_video: str, clips: dict, output_yaml_path: str) -> str
#    Generates transcription for each clip and saves the results to a YAML file.
#
# 10. load_app_config() -> dict
#     Loads the application configuration from a JSON or YAML file.
# ==================================================

import os
import sys
import logging
import json
import datetime
import yaml
import tempfile
import time
import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips
import threading
import platform

logger = logging.getLogger(__name__)

print(f"📦 {__name__} imported into {__file__}")


# ==================================================

# ==================================================
# CLIPS CONFIGURATION
# ==================================================
moviepy_config = {
    "clips_directory": "clips/",
    "width": 1280,
    "height": 720,
    "font": "Arial",
    "font_size": 64,
    "text_halign": "left",
    "text_valign": "center",
    "output_format": "mp4",
    "text_color": "white",
}

# ==================================================
# LOGGING INITIALIZATION
# ==================================================
def initialize_logging():
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "tja.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Logging initialized.")
    return logger

def load_app_config():
    """Load the application configuration from a JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(current_dir, "../../")  # 👈 define it here first
    config_path = os.path.join(base_dir, "conf/app_config.json")  # 👈 correct path

    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Base directory not found at {base_dir}")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    try:
        with open(config_path, "r") as file:
            app_config = json.load(file)
        return app_config
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON configuration at {config_path}: {e}")


# ==================================================
# AUDIO EXTRACTION AND CAPTIONING
# ==================================================
def extract_audio_from_video(video_path, start_time, end_time, temp_audio_path):
    video = VideoFileClip(video_path).subclip(start_time, end_time)
    video.audio.write_audiofile(temp_audio_path)
    return temp_audio_path

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except (sr.UnknownValueError, sr.RequestError):
        return ""

def process_clip1(video_path, start_time, end_time):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_path = extract_audio_from_video(video_path, start_time, end_time, temp_audio_file.name)
        transcription = transcribe_audio(audio_path)
        os.remove(audio_path)
        user_input = input(f"Transcribed text: '{transcription}'\nPress Enter to keep or type a new caption: ")
        return user_input.strip() if user_input else transcription



def timed_input(prompt, timeout=10):
    import threading

    result = {"input": None}

    def inner():
        try:
            result["input"] = input(prompt)
        except Exception:
            result["input"] = ''

    thread = threading.Thread(target=inner)
    # DO NOT set daemon=True — that causes this crash
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print(f"\n[Timed out after {timeout} seconds. Using default transcription.]\n")
        return ''
    return result["input"]


def process_clip(video_path, start_time, end_time):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        audio_path = extract_audio_from_video(video_path, start_time, end_time, temp_audio_file.name)
        transcription = transcribe_audio(audio_path)
        os.remove(audio_path)

        user_input = timed_input(
            f"Transcribed text: '{transcription}'\nPress Enter to keep or type a new caption (10s timeout): ",
            timeout=10
        )
        return user_input.strip() if user_input else transcription


# ==================================================
# NEW: Generate Transcripts from Clip Set
# ==================================================
def generate_clip_transcripts(input_video, clips, output_yaml_path, logger=None):
    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]

            if logger:
                logger.info(f"🔊 Processing {clip_name} ({start}s – {end}s)")

            existing_text = clip.get("text", "").strip()

            # Step 1: if text exists, ask user to keep or re-transcribe
            if existing_text:
                print(f"\n⚙️  Existing text for {clip_name}: \"{existing_text}\"")
                use_existing = input("👉 Use this text? (y/n): ").strip().lower()
                if use_existing == "y":
                    if logger:
                        logger.info(f"✅ Keeping existing text: \"{existing_text}\"")
                    continue  # keep existing text, move to next clip

            # Step 2: transcribe audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                audio_path = extract_audio_from_video(input_video, start, end, temp_audio_file.name)
                transcription = transcribe_audio(audio_path)
                os.remove(audio_path)

            # Step 3: confirm or edit transcription
            print(f"\n📝 Transcribed: \"{transcription}\"")
            user_input = input("✏️  Press Enter to accept, or type new caption: ").strip()

            final_text = user_input if user_input else transcription
            clip["text"] = final_text

            if logger:
                logger.info(f"✍️ Final text for {clip_name}: \"{final_text}\"")

    with open(output_yaml_path, "w") as f:
        yaml.dump(clips, f)

    if logger:
        logger.info(f"📝 Updated YAML saved to {output_yaml_path}")

    return output_yaml_path



# ==================================================
# PROCESS CLIPS
# ==================================================
def process_clips_moviepy(config, clips, logger, input_video, output_dir, captions_config=None):
    video_clip = VideoFileClip(input_video)
    clips_directory = os.path.join(output_dir)
    os.makedirs(clips_directory, exist_ok=True)

    # Prefer captions config if provided
    font = (captions_config or config).get("font", "Arial")
    font_size = (captions_config or config).get("font_size", 48)
    text_color = (captions_config or config).get("text_color", "white")
    text_halign = (captions_config or config).get("text_halign", "center")
    text_valign = (captions_config or config).get("text_valign", "bottom")

    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]
            text = process_clip(input_video, start, end)
            clip["text"] = text
            output_file = os.path.join(clips_directory, f"{clip_name}.mp4")
            logger.info(f"Processing Clip: {clip_name} ({start}-{end} sec)")

            clip_segment = video_clip.subclip(start, end)

            if text.strip():
                txt_clip = TextClip(
                    text,
                    fontsize=font_size,
                    font=font,
                    color=text_color
                ).set_position((text_halign, text_valign)).set_duration(clip_segment.duration)
                video_with_text = CompositeVideoClip([clip_segment, txt_clip])
            else:
                video_with_text = clip_segment

            video_with_text.write_videofile(output_file, codec="libx264", audio_codec="aac")
            logger.info(f"✅ Wrote video to: {output_file}")
            logger.info(f"📂 File exists? {os.path.exists(output_file)}")
            logger.info(f"Clip {clip_name} processed successfully.")


def create_output_directory(base_dir="clips"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    input_video_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    output_dir = os.path.join(base_dir, f"{input_video_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def load_clips_from_file(file_path):
    if not os.path.exists(file_path):
        sys.exit(f"Error: Clip file '{file_path}' not found.")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) if file_path.endswith(('.yaml', '.yml')) else json.load(file)

def stitch_clips(clip_files, output_file):
    final_clips = [VideoFileClip(clip) for clip in clip_files]
    final_video = concatenate_videoclips(final_clips, method="compose")
    final_video.write_videofile(output_file, codec="libx264", fps=24, audio_codec="aac")
    print(f"Final stitched video saved as {output_file}")

def process_clips_with_captions(app_config, clips, logger, input_video, output_dir):
    video_clip = VideoFileClip(input_video)
    clips_directory = output_dir  # ✅ No extra "clips" subdir
    os.makedirs(clips_directory, exist_ok=True)
    
    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                audio_path = extract_audio_from_video(input_video, start, end, temp_audio_file.name)
                transcription = transcribe_audio(audio_path)
                os.remove(audio_path)
            
            if transcription:
                logger.info(f"Clip {clip_name}: Transcription -> {transcription}")
                clip["text"] = transcription
            
            output_file = os.path.join(clips_directory, f"{clip_name}.mp4")
            
            logger.info(f"Processing Clip: {clip_name} ({start}-{end} sec)")
            
            logger.info(f"Applying captions using external module...")
            captions_config = app_config.get("captions", {})
            captions_config["input_video_path"] = output_file
            captions_config["download_path"] = clips_directory
            captions_config["paragraph"] = transcription
            
            from basic_captions3 import add_captions
            result = add_captions(captions_config, logger)
            if result:
                logger.info(f"Captioning completed: {result['to_process']}")
            else:
                logger.error("Captioning failed.")

def create_subdir(base_dir="clips", subdir_name="orange"):
    """
    Creates a subdirectory with a custom name inside a timestamped folder
    based on the input video name. Returns the full path to the subdir.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    input_video_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    root_output = os.path.join(base_dir, f"{input_video_name}_{timestamp}")
    subdir_timestamp = datetime.datetime.now().strftime("%H%M%S")  # add short time to subdir
    full_subdir_name = f"{subdir_name}_{subdir_timestamp}"  # e.g. orange_165314
    subdir_path = os.path.join(root_output, full_subdir_name)
    os.makedirs(subdir_path, exist_ok=True)
    return subdir_path

# Load Platform-Specific Configuration
def load_config():
    """Load configuration based on the operating system."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../../conf/config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as file:
        config = json.load(file)

    os_name = platform.system()
    if os_name not in config:
        raise ValueError(f"Unsupported platform: {os_name}")

    return config[os_name]

def process_clips_with_captions(config, clips, logger, input_video, output_dir):
    """
    Process clips with transcription and captioning
    Args:
        config (dict): Full app config
        clips (dict): Dictionary of clip name -> clip list with start/end
        logger (Logger): Logger object
        input_video (str): Path to the input video
        output_dir (str): Directory to save output clips
    """
    video_clip = VideoFileClip(input_video)
    clips_directory = os.path.join(output_dir, "clips")
    os.makedirs(clips_directory, exist_ok=True)

    for clip_name, clip_list in clips.items():
        for clip in clip_list:
            start, end = clip["start"], clip["end"]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                audio_path = extract_audio_from_video(input_video, start, end, temp_audio_file.name)
                transcription = transcribe_audio(audio_path)
                os.remove(audio_path)

            if transcription:
                logger.info(f"Clip {clip_name}: Transcription -> {transcription}")
                clip["text"] = transcription

            output_file = os.path.join(clips_directory, f"{clip_name}.mp4")
            logger.info(f"Processing Clip: {clip_name} ({start}-{end} sec)")

            # Step 1: Extract subclip and write to disk before captioning
            clip_segment = video_clip.subclip(start, end)
            clip_segment.write_videofile(output_file, codec="libx264", audio_codec="aac")

            # Step 2: Feed the written clip into the captioning pipeline
            logger.info(f"Applying captions using external module...")
            captions_config = config.get("captions", {}).copy()
            captions_config["input_video_path"] = output_file
            captions_config["download_path"] = clips_directory
            captions_config["paragraph"] = transcription

            from basic_captions3 import add_captions
            result = add_captions(captions_config, logger)
            if result:
                logger.info(f"Captioning completed: {result['to_process']}")
            else:
                logger.error("Captioning failed.")


