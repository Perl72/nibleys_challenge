
import os
import sys
import json
import logging
from difflib import SequenceMatcher

# === Load from local utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from utilities1 import initialize_logging, load_app_config

# === Translation dependencies ===
from transformers import MarianMTModel, MarianTokenizer

# === Load translation model ===
model_name = "Helsinki-NLP/opus-mt-es-en"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# === Helper: Translate a text chunk ===
def translate_text(text):
    if not text.strip():
        return ""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

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

# === Helper: Load and translate transcript ===
def load_translated_transcript(video_path, logger):
    base = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = f"data/{base}.minute.json"
    output_txt_path = f"data/{base}.translated.en.txt"

    if not os.path.exists(transcript_path):
        logger.error(f"Transcript not found at {transcript_path}")
        return ""

    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        chunks = [
            translate_text(v.get("text", "") if isinstance(v, dict) else str(v))
            for k, v in sorted(data.items())
        ]
        full_text = " ".join(chunks)

        with open(output_txt_path, "w", encoding="utf-8") as out_file:
            out_file.write(full_text)
            logger.info(f"Saved translated transcript to {output_txt_path}")

        logger.info(f"Translated {len(chunks)} chunks to English ({len(full_text)} characters)")
        logger.debug(f"Translated preview: {full_text[:300]}")
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
            logger.error("Usage: python translate_and_compare.py <video_file_path>")
            sys.exit(1)

        input_video_path = sys.argv[1]
        if not os.path.isfile(input_video_path):
            logger.error(f"Video file does not exist: {input_video_path}")
            sys.exit(1)

        logger.info(f"Processing video file: {input_video_path}")

        article_dir = "sources/mimesis/20250527-232733/articles/20250527-232733"

        articles = load_articles(article_dir, logger)
        transcript = load_translated_transcript(input_video_path, logger)

        logger.info("\n--- Transcript to Article Similarity (Translated) ---")
        for name, content in articles.items():
            sim = compare_texts(transcript, content)
            logger.info(f"Translated Transcript ↔ {name}: {sim:.3f}")

        logger.info("Comparison complete.")

    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        sys.exit(1)
