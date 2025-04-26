import sys
import time
import re
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def fetch_mp3_from_page(url, download_dir="downloads"):
    os.makedirs(download_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless")  # comment this out if you want to see the browser
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")

    print("[🌐] Launching headless Chrome...")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    print("[🕒] Waiting for page to load through Cloudflare...")
    time.sleep(5)  # You can tune this depending on how long Cloudflare takes

    page_html = driver.page_source
    driver.quit()

    mp3_links = re.findall(r'https?://[^"\']+\.mp3', page_html)
    if not mp3_links:
        print("[❌] No .mp3 files found.")
        return None

    mp3_url = mp3_links[0]
    filename = os.path.join(download_dir, os.path.basename(mp3_url.split("?")[0]))
    print(f"[🎧] Downloading {mp3_url} to {filename}")

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
    fetch_mp3_from_page(podcast_url)

