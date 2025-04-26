# call_whisper_transcribe.py — now Whisper-powered 🧠
# this script compares 4 versions of TB's "every-story"
# data/original is from 2025! as they rolled out the same script
# 3 sources from 2019 gathered
# 

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



from transcription_utils import (
    whisper_transcribe_full_video,
    whisper_transcribe_video_by_minute,
   
)

from utilities1 import (
    initialize_logging,
    load_app_config,
    create_output_directory,
    create_subdir,
    distill_run_snapshot
)


# Initialize the logger
logger = initialize_logging()

# === CLI Entry Point ===
if len(sys.argv) < 2:
    print("Usage: python call_whisper_transcribe.py <input_video>")
    sys.exit(1)

input_video = sys.argv[1]
config = load_app_config()




# === Set up output directories ===
base_output_dir= create_subdir(base_dir="sources", subdir_name="mimesis")
#base_output_dir = create_output_directory(input_video, config)
article_dir = create_subdir(base_output_dir, "articles")

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

# === Editorial Content Scraping ===
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

urls = [
    "https://www.deseret.com/2019/2/4/20664993/tim-ballard-i-ve-fought-sex-trafficking-at-the-border-this-is-why-we-need-a-wall/",
    "https://www.foxnews.com/opinion/ive-fought-sex-trafficking-as-a-dhs-special-agent-we-need-to-build-the-wall-for-the-children",
    "https://www.presidency.ucsb.edu/documents/remarks-meeting-human-trafficking-the-mexico-united-states-border-and-exchange-with?utm_source=chatgpt.com"
]

print("\n=== Scraping Articles ===")
for url in urls:
    print(f"→ {url}")
    element = extract_editorial_content(url)

    if not element:
        print("❌ Failed to fetch.")
        continue

    slug = slugify_url(url)
    plain_text = element.get_text("\n", strip=True)
    italics = get_text_with_italics(element)
    raw_html = element.prettify()

    with open(os.path.join(article_dir, f"{slug}.txt"), "w", encoding="utf-8") as f:
        f.write(plain_text)

    with open(os.path.join(article_dir, f"{slug}-italics.txt"), "w", encoding="utf-8") as f:
        f.write(italics)

    with open(os.path.join(article_dir, f"{slug}-html.txt"), "w", encoding="utf-8") as f:
        f.write(raw_html)

    print(f"   ✅ Saved to: {article_dir}/{slug}*.txt")
    
if __name__ == "__main__":
    main()
