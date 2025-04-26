import os
import sys
import json
import traceback
from datetime import datetime

# === Load from local utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from utilities2 import initialize_logging,load_app_config
from utilities4 import update_task_output_path, add_default_tasks_to_metadata

# === Attempt to import watermarking function ===
try:
    from watermarker2 import add_watermark
except ImportError as e:
    print(f"Failed to import add_watermark: {e}")
    sys.exit(1)

# === MAIN EXECUTION ===
if __name__ == "__main__":
    try:
        # Load app configuration
        app_config = load_app_config()
        watermark_config = app_config.get("watermark_config", {})
        logger = initialize_logging()

        # Validate input arguments
        if len(sys.argv) < 2:
            logger.error("Usage: python call_watermark.py <video_file_path>")
            sys.exit(1)

        input_video_path = sys.argv[1]
        if not os.path.isfile(input_video_path):
            logger.error(f"Input video file does not exist: {input_video_path}")
            sys.exit(1)

        logger.info(f"Processing video file: {input_video_path}")

        # Locate and read metadata JSON
        # Fallback: guess based on input path
        json_path = os.path.join("metadata", os.path.basename(input_video_path).replace(".mp4", ".json"))

        logger.info(f"Looking for metadata file: {json_path}")

        if not os.path.isfile(json_path):
            logger.error(f"Metadata file not found: {json_path}")
            sys.exit(1)

        try:
            with open(json_path, "r") as file:
                data = json.load(file)
            logger.info(f"Loaded metadata from: {json_path}")
            username = data.get("uploader", "UnknownUploader")
            video_date = data.get("video_date", datetime.now().strftime("%Y-%m-%d"))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON metadata from {json_path}: {e}")
            sys.exit(1)

        # Prepare parameters for watermarking
        params = {
            "input_video_path": input_video_path,
            "download_path": os.path.dirname(input_video_path),
            "username": username,
            "video_date": video_date,
            **watermark_config,
        }

        logger.debug(f"Watermark configuration: {watermark_config}")

        # Perform watermarking
        logger.info("Starting watermarking process...")
        result = add_watermark(params)

        if result and "to_process" in result:
            output_path = result["to_process"]
            logger.info(f"Watermarked video created successfully: {output_path}")
            print(output_path)

            # Make sure default_tasks is initialized
            add_default_tasks_to_metadata(json_path)

            # Update metadata with output path
            update_result = update_task_output_path(json_path, "apply_watermark", output_path)
            logger.debug(f"Metadata update result: {update_result}")
        else:
            logger.error("Watermarking process failed or did not return valid output.")
            sys.exit(1)

    except Exception as e:
        if 'logger' in globals():
            logger.error(f"An unexpected error occurred: {e}")
            logger.debug(traceback.format_exc())
        else:
            print(f"Unexpected error: {e}")
            print(traceback.format_exc())
        sys.exit(1)
