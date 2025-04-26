import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# === Path Setup ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

# === Imports from shared utils ===
from utilities2 import initialize_logging, load_app_config
from utilities3 import extract_audio_from_video, transcribe_audio, generate_dynamic_clips_from_metadata

# Initialize logger
logger = initialize_logging()




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
# MAIN
# ==================================================
if len(sys.argv) < 2:
    print("Usage: python call_captions.py <video_path>")
    sys.exit(1)


# Validate video path argument
video_path = sys.argv[1]
video_name = os.path.basename(video_path).replace(".mp4", "")
json_path = os.path.join("metadata", f"{video_name}.json")

# Load app configuration
app_config = load_app_config()

# Extract watermark and captions configuration from app config
watermark_config = app_config.get("watermark_config", {})
caption_config = app_config.get("captions", {})

# Check for metadata file
if not os.path.exists(json_path):
    logger.error(f"Metadata not found: {json_path}")
    sys.exit(1)

# Read and load metadata from the JSON file
with open(json_path, "r") as f:
    metadata = json.load(f)

# Check for clips in metadata
clips = metadata.get("clips", [])
if not clips:
    logger.warning("No clips defined in metadata.")
    sys.exit(1)

logger.info(f"🧩 Found {len(clips)} clips in metadata. Starting caption overlay...")

# Use the proper output directory derived from video metadata
output_dir = metadata.get("output_dir") or moviepy_config["clips_directory"]

# Process each clip
for clip in clips:
    clip_name = clip["name"]
    clip_file = os.path.join(output_dir, f"{clip_name}.mp4")
    output_captioned = os.path.join(output_dir, f"{clip_name}_captioned.mp4")

    if not os.path.exists(clip_file):
        logger.warning(f"Clip file missing: {clip_file}")
        continue

    logger.info(f"🎬 Processing clip: {clip_file}")

    # Create a temporary file for audio extraction
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio_path = temp_audio.name

    try:
        # Extract audio from video and transcribe it
        extract_audio_from_video(clip_file, 0, None, temp_audio_path)
        transcription = transcribe_audio(temp_audio_path)
        os.remove(temp_audio_path)

        if not transcription:
            transcription = clip.get("text", "(No transcription)")

        # Create the video with the caption overlay
        clip_video = VideoFileClip(clip_file)
        txt_clip = TextClip(transcription, fontsize=moviepy_config["font_size"],
                            font=moviepy_config["font"], color=moviepy_config["text_color"])
        txt_clip = txt_clip.set_position((moviepy_config["text_halign"], moviepy_config["text_valign"]))
        txt_clip = txt_clip.set_duration(clip_video.duration)

        final = CompositeVideoClip([clip_video, txt_clip])
        final.write_videofile(output_captioned, codec="libx264", audio_codec="aac")

        logger.info(f"✅ Captioned clip saved: {output_captioned}")

    except Exception as e:
        logger.error(f"❌ Failed to process {clip_file}: {e}")
        continue
