
import os
import json
import logging
from difflib import SequenceMatcher
from datetime import datetime

# === Setup Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# === Paths ===
article_dir = "sources/mimesis/20250527-232733/articles/20250527-232733"
transcript_path = "data/Tim_Ballard_20250526_watermarked.minute.json"

# === Utility: Load article texts ===
def load_articles():
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

# === Utility: Load transcript from flexible formats ===
def load_transcript():
    if not os.path.exists(transcript_path):
        logger.error("Transcript file not found.")
        return ""
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            # Support both: { "0-60s": "text" } and { "0-60s": {"text": "..." } }
            full_text = " ".join(
                [v.get("text", "") if isinstance(v, dict) else str(v) for k, v in sorted(data.items())]
            )
            logger.info(f"Loaded transcript with {len(data)} chunks, {len(full_text)} characters")
            logger.debug(f"Transcript preview: {full_text[:300]}")
            return full_text
        else:
            logger.error("Unexpected transcript format.")
            return ""

# === Utility: Compare two texts ===
def compare_texts(t1, t2):
    return SequenceMatcher(None, t1, t2).ratio()

# === Main Routine ===
def main():
    logger.info("Starting document similarity analysis...")

    articles = load_articles()
    transcript = load_transcript()

    # === Article-to-Article comparisons ===
    logger.info("\n--- Article to Article Similarity ---")
    keys = list(articles.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            k1, k2 = keys[i], keys[j]
            sim = compare_texts(articles[k1], articles[k2])
            logger.info(f"{k1} ↔ {k2}: {sim:.3f}")

    # === Transcript-to-Article comparisons ===
    logger.info("\n--- Transcript to Article Similarity ---")
    for name, content in articles.items():
        sim = compare_texts(transcript, content)
        logger.info(f"Transcript ↔ {name}: {sim:.3f}")

    logger.info("Comparison complete.")

if __name__ == "__main__":
    main()
