# call_whisper_transcribe.py — now Whisper-powered 🧠
# This script compares 4 versions of TB's "every-story"
# data/original is from 2025! as they rolled out the same script
# 3 sources from 2019 gathered

import sys
import json
import os
import logging
import traceback
import requests
import re
from datetime import datetime
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from bs4 import BeautifulSoup

# === Load from local utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from transcription_utils import (
    whisper_transcribe_full_video,
    whisper_transcribe_video_by_minute,
    distill_run_snapshot,
    write_srt,
    write_vtt,
    extract_editorial_content,
    slugify_url,
    get_text_with_italics,

)

from utilities1 import (
    initialize_logging,
    load_app_config,
    create_output_directory,
    create_subdir,
)

# === Initialize logger ===
logger = initialize_logging()


# === Main ===

def main():
    if len(sys.argv) < 2:
        print("Usage: python call_whisper_transcribe.py <input_video>")
        sys.exit(1)

    input_video = sys.argv[1]
    config = load_app_config()

    base_output_dir = create_subdir(base_dir="sources", subdir_name="mimesis")
    article_dir = create_subdir(base_output_dir, "articles")

    logger.info(f"Base output directory: {base_output_dir}")
    logger.info(f"Article subdir: {article_dir}")

    video_stem = os.path.splitext(os.path.basename(input_video))[0]
    full_outfile = os.path.join(base_output_dir, f"{video_stem}.full.txt")
    minute_outfile = os.path.join(base_output_dir, f"{video_stem}.minute.json")

    # === Transcribe full video ===
    logger.info("Starting full video transcription...")
    try:
        full_transcript = whisper_transcribe_full_video(input_video)
        with open(full_outfile, "w") as f:
            f.write(full_transcript)
        logger.info(f"Full transcript saved to {full_outfile}")
    except Exception:
        logger.error("Failed full video transcription")
        logger.debug(traceback.format_exc())

    # === Transcribe by minute ===
    logger.info("Starting minute-by-minute transcription...")
    try:
        minute_transcript = whisper_transcribe_video_by_minute(input_video)
        with open(minute_outfile, "w") as f:
            json.dump(minute_transcript, f, indent=2)
        logger.info(f"Minute-by-minute transcript saved to {minute_outfile}")
    except Exception:
        logger.error("Failed minute-by-minute transcription")
        logger.debug(traceback.format_exc())

    # === Scrape Articles ===
    logger.info("Beginning article scraping...")

    urls = [
        "https://www.deseret.com/2019/2/4/20664993/tim-ballard-i-ve-fought-sex-trafficking-at-the-border-this-is-why-we-need-a-wall/",
        "https://www.foxnews.com/opinion/ive-fought-sex-trafficking-as-a-dhs-special-agent-we-need-to-build-the-wall-for-the-children",
        "https://www.presidency.ucsb.edu/documents/remarks-meeting-human-trafficking-the-mexico-united-states-border-and-exchange-with?utm_source=chatgpt.com"
    ]

    for url in urls:
        logger.info(f"Scraping: {url}")
        element = extract_editorial_content(url)

        if not element:
            logger.warning(f"Skipping due to failed content extraction: {url}")
            continue

        slug = slugify_url(url)
        try:
            plain_text = element.get_text("\n", strip=True)
            italics = get_text_with_italics(element)
            raw_html = element.prettify()

            with open(os.path.join(article_dir, f"{slug}.txt"), "w", encoding="utf-8") as f:
                f.write(plain_text)
            with open(os.path.join(article_dir, f"{slug}-italics.txt"), "w", encoding="utf-8") as f:
                f.write(italics)
            with open(os.path.join(article_dir, f"{slug}-html.txt"), "w", encoding="utf-8") as f:
                f.write(raw_html)

            logger.info(f"Saved article: {slug} (txt, italics, html)")
        except Exception:
            logger.error(f"Failed to save output for {slug}")
            logger.debug(traceback.format_exc())
    # === Generate SRT and VTT from Whisper segments ===
    logger.info("Generating SRT and VTT subtitle files...")
    try:
        import whisper
        model = whisper.load_model("base")  # or "medium"/"large" if you prefer
        whisper_result = model.transcribe(input_video)
        segments = whisper_result['segments']

        srt_outfile = os.path.join(base_output_dir, f"{video_stem}.srt")
        vtt_outfile = os.path.join(base_output_dir, f"{video_stem}.vtt")

        write_srt(segments, srt_outfile)
        write_vtt(segments, vtt_outfile)

        logger.info("Subtitle files written successfully.")
    except Exception:
        logger.error("Failed to generate SRT/VTT subtitles")
        logger.debug(traceback.format_exc())

    # === Create Snapshot ===
    logger.info("📦 Creating snapshot of run...")
    try:
        distill_run_snapshot(base_output_dir, input_video, urls, config)
    except Exception:
        logger.warning("Failed to create snapshot")
        logger.debug(traceback.format_exc())

    logger.info("🎉 Done.")

if __name__ == "__main__":
    main()




