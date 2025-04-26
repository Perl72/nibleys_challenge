import os
import sys
import json
import logging
import traceback
from datetime import datetime

# === Load from local utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from utilities2 import initialize_logging, load_app_config
from tasks_lib import get_task_states, find_url_json

# Initialize the logger
logger = initialize_logging()

# === MAIN EXECUTION ===
from tasks_lib import find_url_json, get_task_states

def main():
    try:
        app_config = load_app_config()

        if len(sys.argv) < 2:
            logger.error("Usage: python continue_tasks.py <instagram_url>")
            sys.exit(1)

        url = sys.argv[1]

        if not url.startswith("http"):
            logger.error(f"❌ Input must be an Instagram URL, not: {url}")
            sys.exit(1)

        logger.info(f"📎 Processing URL: {url}")

        # Look for matching metadata
        json_path, metadata = find_url_json(url)

        if not json_path or not metadata:
            logger.warning(f"⚠️ No metadata found for URL: {url} — skipping.")
            sys.exit(0)

        logger.info(f"✅ Metadata found: {json_path}")

        task_states = metadata.get("default_tasks", {})
        video_path = task_states.get("perform_download")

        if not video_path or not os.path.isfile(video_path):
            logger.warning(f"⚠️ Video file not found: {video_path} — skipping.")
            sys.exit(0)

        logger.info(f"🎬 Found video path: {video_path}")

        # Define task order
        task_order = ["perform_download", "apply_watermark", "generate_captions", "post_processed"]

        for task in task_order:
            val = task_states.get(task)
            if val is True:
                logger.info(f"🔧 Next task to run: {task}")
                # TODO: Replace this with actual task function
                logger.info(f"✨ Simulated running task: {task} for {url}")
                break
            elif isinstance(val, str):
                logger.info(f"✅ Task already completed: {task} → {val}")
            else:
                logger.debug(f"⏩ Task '{task}' not ready or missing.")

        logger.info(f"🏁 Task check complete for: {url}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)



if __name__ == "__main__":
    main()

