import sys
import os
import re
import time
import json
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def fetch_mp3_from_network(url, download_dir="downloads"):
    os.makedirs(download_dir, exist_ok=True)

    print("[🌐] Launching headless Chrome with network logging...")

    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(desired_capabilities=caps, options=options)
    driver.get(url)

    print("[🕒] Waiting for page to fully load through Cloudflare...")
    time.sleep(8)  # allow JS and players to kick in

    logs = driver.get_log("performance")
    driver.quit()

    print(f"[📡] Scanned {len(logs)} network log entries...")

    mp3_urls = []

    for entry in logs:
        try:
            message = json.loads(entry["message"])["message"]
            url_fragment = message.get("params", {}).get("request", {}).get("url", "")
            if ".mp3" in url_fragment:
                mp3_urls.append(url_fragment)
        except Exception:
            continue

    if not mp3_urls:
        print("[❌] No .mp3 URLs found in network traffic.")
        return None

    mp3_url = mp3_urls[0]
    print(f"[🎧] Found MP3: {mp3_url}")

    filename = os.path.join(download_dir, os.path.basename(mp3_url.split("?")[0]))

    print(f"[⬇️] Downloading to: {filename}")
    with requests.get(mp3_url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"[✅] Download complete: {filename}")
    return filename

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_podcast_with_selenium.py <podcast_url>")
        sys.exit(1)

    podcast_url = sys.argv[1]
    fetch_mp3_from_network(podcast_url)
