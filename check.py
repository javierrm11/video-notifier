import json
import os
import subprocess
import sys

import feedparser
import requests

STATE_FILE = "last_video.json"

YOUTUBE_CHANNEL_ID = os.environ["YOUTUBE_CHANNEL_ID"]
TIKTOK_USERNAME = os.environ["TIKTOK_USERNAME"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def get_latest_youtube_video():
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
    feed = feedparser.parse(url)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    return {"id": entry.yt_videoid, "link": entry.link}


def get_latest_tiktok_video():
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "-J",
        f"https://www.tiktok.com/@{TIKTOK_USERNAME}",
    ]

    cookies_file = os.environ.get("TIKTOK_COOKIES_FILE")
    if cookies_file and os.path.exists(cookies_file):
        cmd[1:1] = ["--cookies", cookies_file]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp falló: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    entries = data.get("entries") or []
    if not entries:
        return None
    entry = entries[0]
    video_id = entry["id"]
    link = entry.get("url") or entry.get("webpage_url") or (
        f"https://www.tiktok.com/@{TIKTOK_USERNAME}/video/{video_id}"
    )
    return {"id": video_id, "link": link}


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": False},
        timeout=15,
    )
    resp.raise_for_status()


def main():
    state = load_state()
    changed = False

    youtube_video = get_latest_youtube_video()
    if youtube_video and youtube_video["id"] != state.get("youtube"):
        send_telegram_message(f"🎬 Nuevo vídeo en YouTube:\n{youtube_video['link']}")
        state["youtube"] = youtube_video["id"]
        changed = True

    try:
        tiktok_video = get_latest_tiktok_video()
    except Exception as exc:
        print(f"Aviso: no se pudo comprobar TikTok: {exc}", file=sys.stderr)
        tiktok_video = None

    if tiktok_video and tiktok_video["id"] != state.get("tiktok"):
        send_telegram_message(f"🎵 Nuevo vídeo en TikTok:\n{tiktok_video['link']}")
        state["tiktok"] = tiktok_video["id"]
        changed = True

    if changed:
        save_state(state)
        print("Estado actualizado.")
    else:
        print("Sin novedades.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
