
import os
import sys
import json
import logging
from difflib import SequenceMatcher
from datetime import datetime

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
    distill_run_snapshot,
)

# === Helper: Load articles ===
def load_articles(article_dir, logger):
    articles = {}
    for name in ["deseret", "foxnews", "presidency"]:
        match = next((f for f in os.listdir(article_dir) if name in f), None)
        if match:
            path = os.path.join(article_dir, match)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                articles[name] = content
                logger.info(f"Loaded {name} ({len(content)} characters)")
        else:
            articles[name] = ""
            logger.warning(f"Missing article for {name}")
    return articles

# === Helper: Load transcript from dynamic path ===
def load_transcript(video_path, logger):
    base = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = f"data/{base}.minute.json"

    if not os.path.exists(transcript_path):
        logger.error(f"Transcript not found at {transcript_path}")
        return ""

    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            chunks = [
                v.get("text", "") if isinstance(v, dict) else str(v)
                for k, v in sorted(data.items())
            ]
            full_text = " ".join(chunks)
            logger.info(f"Loaded transcript with {len(data)} chunks, {len(full_text)} characters")
            logger.debug(f"Transcript preview: {full_text[:300]}")
            return full_text
        else:
            logger.error("Unexpected transcript format.")
            return ""

# === Helper: Compare two texts ===
def compare_texts(t1, t2):
    return SequenceMatcher(None, t1, t2).ratio()

# === MAIN EXECUTION ===
if __name__ == "__main__":
    try:
        app_config = load_app_config()
        logger = initialize_logging()

        if len(sys.argv) < 2:
            logger.error("Usage: python script.py <video_file_path>")
            sys.exit(1)

        input_video_path = sys.argv[1]
        if not os.path.isfile(input_video_path):
            logger.error(f"Video file does not exist: {input_video_path}")
            sys.exit(1)

        logger.info(f"Processing video file: {input_video_path}")

        # Get dynamic article path from config or hardcoded fallback
        article_dir = "sources/mimesis/20250527-232733/articles/20250527-232733"

        articles = load_articles(article_dir, logger)
        transcript = load_transcript(input_video_path, logger)

        logger.info("\n--- Article to Article Similarity ---")
        keys = list(articles.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                sim = compare_texts(articles[k1], articles[k2])
                logger.info(f"{k1} ↔ {k2}: {sim:.3f}")

        logger.info("\n--- Transcript to Article Similarity ---")
        for name, content in articles.items():
            sim = compare_texts(transcript, content)
            logger.info(f"Transcript ↔ {name}: {sim:.3f}")

        logger.info("Comparison complete.")

    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
