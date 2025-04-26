# utilities1.py

import os
import time
import traceback
import logging
import json
import logging
import sys
from datetime import datetime


logger = logging.getLogger(__name__)


# Function to store params as a JSON file in the output directory
def store_params_as_json(params):
    """
    Stores the params dictionary as a JSON file in the output directory.
    The filename should match the video file, but with a .json extension.

    Args:
        params (dict): The parameters dictionary to store.

    Returns:
        dict: A dictionary with key 'config_json' and value as the path of the JSON file.
    """
    try:
        original_filename = params.get("original_filename")
        if original_filename:
            json_filename = os.path.splitext(original_filename)[0] + ".json"
            with open(json_filename, "w") as json_file:
                json.dump(params, json_file, indent=4)
            logger.info(f"Params saved to JSON file: {json_filename}")
            return {"config_json": json_filename}
        else:
            logger.warning("No original filename found in params to create JSON file.")
            return {"config_json": None}
    except Exception as e:
        logger.error(f"Failed to save params to JSON: {e}")
        logger.debug(traceback.format_exc())
        return {"config_json": None}


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


def print_params(params):
    """
    Prints parameters for diagnostic purposes.

    Args:
        params (dict): Parameters to print.
    """
    print("Received parameters:")
    for key, value in params.items():
        print(f"{key}: {value}")


def handle_exception(e):
    """
    Handles exceptions by printing the error message and traceback.

    Args:
        e (Exception): The exception to handle.
    """
    print(f"Error: {e}")
    traceback.print_exc()


def current_timestamp():
    """
    Returns the current timestamp in a readable format.

    Returns:
        str: Current timestamp as a formatted string.
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def on_progress(stream, chunk, bytes_remaining):
    """
    Callback function to report download progress.

    Args:
        stream: The stream being downloaded.
        chunk: The chunk of data that has been downloaded.
        bytes_remaining (int): Number of bytes remaining to download.
    """
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(f"Download progress: {percentage_of_completion:.2f}%")


def on_complete(stream, file_path):
    """
    Callback function when a download is complete.

    Args:
        stream: The stream that was downloaded.
        file_path (str): Path to the downloaded file.
    """
    print(f"Download complete: {file_path}")

# ==================================================
# LOGGING INITIALIZATION
# ==================================================
def initialize_logging():
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "tja.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Logging initialized.")
    return logger


def load_app_config():
    """Load the application configuration from a JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(current_dir, "../../")
    
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Base directory not found at {base_dir}")
    
    config_path = os.path.join(base_dir, "conf/app_config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    try:
        with open(config_path, "r") as file:
            app_config = json.load(file)
        return app_config
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON configuration at {config_path}: {e}")




def create_subdir(base_dir="sources", subdir_name=None):
    """
    Creates a subdir like sources/<subdir_name>/<timestamp>.
    If subdir_name is not provided, tries sys.argv[1], or defaults to 'default'.
    """
    try:
        input_video_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    except IndexError:
        input_video_name = "default"

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_name = subdir_name if subdir_name else input_video_name
    output_dir = os.path.join(base_dir, folder_name, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    return output_dir



# Load Platform-Specific Configuration
def load_config():
    """Load configuration based on the operating system."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "../conf/config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r") as file:
        config = json.load(file)

    os_name = platform.system()
    if os_name not in config:
        raise ValueError(f"Unsupported platform: {os_name}")

    return config[os_name]





def create_output_directory(base_dir="clips"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_video_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    output_dir = os.path.join(base_dir, f"{input_video_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def distill_run_snapshot(output_dir, input_video, urls, config):
    import socket
    import getpass
    import platform
    import subprocess

    tb_dir = os.path.join(output_dir, "tb")
    os.makedirs(tb_dir, exist_ok=True)

    # Basic metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_video": input_video,
        "urls_scraped": urls,
        "user": getpass.getuser(),
        "hostname": socket.gethostname(),
        "platform": platform.platform()
    }

    # Write main summary
    with open(os.path.join(tb_dir, "snapshot.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Save app config
    try:
        with open(os.path.join(tb_dir, "config_app.json"), "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.warning("Could not dump config_app.json")

    # Try to copy platform config if it exists
    platform_config_path = os.path.join(current_dir, "../conf/config.json")
    if os.path.exists(platform_config_path):
        try:
            with open(platform_config_path, "r") as f:
                platform_config = json.load(f)
            with open(os.path.join(tb_dir, "config_platform.json"), "w") as f:
                json.dump(platform_config, f, indent=2)
        except Exception:
            logger.warning("Could not copy platform config")

    # Save env snapshot
    try:
        result = subprocess.run(["pip", "freeze"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        with open(os.path.join(tb_dir, "env.txt"), "w") as f:
            f.write(result.stdout)
    except Exception:
        logger.warning("Could not generate pip freeze")

    logger.info(f"📦 Snapshot saved in {tb_dir}")


