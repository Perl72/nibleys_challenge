# downloader5.py
# mask_metadata calls extract_metadata
# works with 10.caller.py
# adding logging

import yt_dlp
import requests
import os
import json
import traceback
import time
import logging

####################
# Logger setup
# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
###########################








def unique_output_path(path, filename):
    """
    Generates a unique output file path by appending a counter to the filename if it already exists.

    Args:
        path (str): Directory path.
        filename (str): Original filename.

    Returns:
        str: A unique file path.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(path, unique_filename)):
        unique_filename = f"{base}_{counter}{ext}"
        counter += 1
    return os.path.join(path, unique_filename)


def extract_metadata(params):
    """
    Extracts all available metadata from a YouTube video without downloading it and saves it to a file.

    Args:
        params (dict): Parameters for extracting metadata, including:
            - url (str): Video URL.
            - metadata_path (str): Path to save the metadata JSON file.
            - cookie_path (str): Path to the cookie file (optional).

    Returns:
        dict: A dictionary containing all available metadata about the video.
    """
    logger.info("Received parameters for metadata extraction:")
    for key, value in params.items():
        logger.info(f"{key}: {value}")

    url = params.get("url")
    cookie_path = params.get("cookie_path")
    metadata_path = params.get("metadata_path")

    try:
        # Set up yt-dlp options for extracting metadata
        ydl_opts = {
            "cookiefile": (
                cookie_path if cookie_path and os.path.exists(cookie_path) else None
            ),
            "noplaylist": True,  # Ensure only the single video is processed if the URL is a playlist
            "skip_download": True,  # Skip actual video download
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(
                url, download=False
            )  # Extract metadata without downloading

            # Save metadata to file
            if metadata_path:
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(info_dict, f, indent=4, ensure_ascii=False)
                logger.info(f"Metadata saved to {metadata_path}")

            return info_dict
    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        logger.debug(traceback.format_exc())
        return {}


# New function to mask metadata
def mask_metadata(params):
    """
    Masks certain metadata for privacy and returns the masked data.

    Args:
        params (dict): The input dictionary containing metadata.

    Returns:
        dict: A dictionary containing masked metadata fields.
    """
   

    logger.info("Masking metadata")
    masked_metadata = {}

    # Extract metadata
    metadata = extract_metadata(params)  # ✅ Indented properly
    if metadata:
        normalized_metadata = {}

        key_mapping = {
            "video_title": ["title"],
            "video_date": ["upload_date"],
            "uploader": ["uploader", "uploader_id"],
            "file_path": ["file_path"],
            "duration": ["duration"],
            "width": ["width"],
            "height": ["height"],
            "ext": ["ext"],
            "resolution": ["resolution"],
            "fps": ["fps"],
            "channels": ["channels"],
            "filesize": ["filesize"],
            "tbr": ["tbr"],
            "protocol": ["protocol"],
            "vcodec": ["vcodec"],
            "vbr": ["vbr"],
            "acodec": ["acodec"],
            "abr": ["abr"],
            "asr": ["asr"],
        }

        # Normalize metadata values
        for standard_key, possible_keys in key_mapping.items():
            for key in possible_keys:
                if key in metadata:
                    normalized_metadata[standard_key] = metadata[key]
                    break  # Stop at the first found key

        # Process video title separately (replace spaces)
        if "video_title" in normalized_metadata:
            normalized_metadata["video_title"] = normalized_metadata["video_title"].replace(" ", "_")

        logger.info("Extracted and normalized metadata:")
        for key, value in normalized_metadata.items():
            logger.info(f"{key}: {value}")

        return normalized_metadata  # ✅ Now properly inside the function



def get_codecs_by_extension(extension):
    # Determine codecs based on file extension
    codecs = {
        ".webm": {"video_codec": "libvpx", "audio_codec": "libvorbis"},
        ".mp4": {"video_codec": "libx264", "audio_codec": "aac"},
        ".ogv": {"video_codec": "libtheora", "audio_codec": "libvorbis"},
        ".mkv": {"video_codec": "libx264", "audio_codec": "aac"},
    }
    return codecs.get(extension, {"video_codec": "libx264", "audio_codec": "aac"})



def create_original_filename(params):
    """
    Generates an original filename for the video based on parameters and ensures a fallback name if uploader is missing.

    Args:
        params (dict): The input dictionary containing relevant fields.

    Returns:
        dict: A dictionary containing the original filename.
    """
    # Extract the required fields from params
    download_path = params.get("download_path", "/Volumes/BallardTim/")
    video_uploader = params.get("uploader", "").strip()  # Ensure it's a string and strip whitespace
    video_date = params.get("video_date", "").strip()

    # Ensure valid defaults if uploader or date is missing
    if not video_uploader:
        logger.warning("Uploader missing from metadata, using 'unknown_uploader'.")
        video_uploader = "unknown_uploader"

    if not video_date:
        logger.warning("Video date missing from metadata, using 'unknown_date'.")
        video_date = "unknown_date"

    # Format the uploader name to be filename-safe
    video_uploader_filename = video_uploader.replace(" ", "_").replace("/", "_")
    ext = params.get("ext", "mp4")  # Default to mp4 if not specified

    # Construct the output filename
    output_filename = f"{video_uploader_filename}_{video_date}.{ext}"

    # Generate a unique filename to avoid overwrites
    unique_filename = unique_output_path(download_path, output_filename)

    # Update params with the generated filename
    params["original_filename"] = unique_filename

    logger.info(f"Generated original filename: {unique_filename}")
    return {"original_filename": unique_filename}



def download_video(params):
    """
    Downloads a video from a given URL using yt-dlp.

    Args:
        params (dict): Parameters for the download including:
            - url (str): Video URL.
            - video_download (dict): Video download configuration.

    Returns:
        str: The path to the downloaded video, or None if download fails.
    """
    # Log incoming parameters for diagnostics
    logger.info("Received parameters: download_video:")
    for key, value in params.items():
        logger.info(f"{key}: {value}")

    url = params.get("url")
    video_download_config = params.get("video_download", {})

    if not url:
        logger.error("No URL provided for download.")
        return None

    try:
        start_time = time.time()
        logger.info(f"Starting download for URL: {url}")

        # Set up yt-dlp options for actual download based on video_download_config
        ydl_opts = {
            "outtmpl": params["original_filename"],
            "cookiefile": video_download_config.get("cookie_path"),
            "format": video_download_config.get("format", "bestvideo+bestaudio/best"),
            "noplaylist": video_download_config.get("noplaylist", True),
            "verbose": True,
        }

        logger.debug(f"yt-dlp options: {ydl_opts}")

        # Perform the video download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("About to download video.")
            ydl.download([url])
            logger.info("Video download completed.")

        end_time = time.time()
        logger.info(f"Download completed in {end_time - start_time:.2f} seconds")
        #save params
        #save_params_to_json(params)
        return {"to_process": params["original_filename"]}
    except Exception as e:
        logger.error(f"Failed to download video: {e}")
        logger.debug(traceback.format_exc())
        return None
        

def save_params_to_json(params):
    """
    Saves the parameters as a .json file in the same output directory.

    Args:
        params (dict): Dictionary containing all parameters.
    """
    try:
        # Get the output filename and create the JSON filename by changing the extension to .json
        original_filename = params.get("original_filename")
        if not original_filename:
            logger.error("No original filename found in parameters. Unable to save JSON.")
            return

        # Replace the extension with .json
        json_filename = os.path.splitext(original_filename)[0] + ".json"

        # Save the parameters to a JSON file
        with open(json_filename, "w", encoding="utf-8") as json_file:
            json.dump(params, json_file, indent=4, ensure_ascii=False)

        logger.info(f"Parameters saved to JSON file: {json_filename}")
    except Exception as e:
        logger.error(f"Failed to save parameters to JSON: {e}")
        logger.debug(traceback.format_exc())



