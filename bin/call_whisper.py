# call_whisper_transcribe.py — now Whisper-powered 🧠

import sys
import json
import os
import logging
import tempfile
import traceback
from datetime import datetime
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


# === Load from local utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)


from tasks_lib import get_task_states, find_url_json





from transcription_utils import (
    whisper_transcribe_full_video,
    whisper_transcribe_video_by_minute,
   
)

from utilities1 import (
    initialize_logging,
    load_app_config,
    create_output_directory,
    create_subdir
)


# Initialize the logger
logger = initialize_logging()

# === CLI Entry Point ===
if len(sys.argv) < 2:
    print("Usage: python call_whisper_transcribe.py <input_video>")
    sys.exit(1)

input_video = sys.argv[1]
config = load_app_config()

# === Full Video Transcription (Whisper) ===
print("\n=== Transcribing full video with Whisper ===")
full_transcript = whisper_transcribe_full_video(input_video)
full_outfile = input_video.replace(".mp4", ".full.txt")
with open(full_outfile, "w") as f:
    f.write(full_transcript)
print(f"📝 Full transcript saved to {full_outfile}")

# === Minute-by-Minute Transcription (Whisper) ===
print("\n=== Transcribing by minute with Whisper ===")
minute_transcript = whisper_transcribe_video_by_minute(input_video)
minute_outfile = input_video.replace(".mp4", ".minute.json")
with open(minute_outfile, "w") as f:
    json.dump(minute_transcript, f, indent=2)
print(f"📝 Minute transcript saved to {minute_outfile}")

