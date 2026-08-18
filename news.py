import os
import sys

import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "llm",
    "gpt",
    "openai",
    "anthropic",
    "claude",
    "programming",
    "developer",
    "software",
    "python",
    "javascript",
    "typescript",
    "coding",
    "code",
]

MAX_STORIES_TO_CHECK = 50


def matches_keywords(title):
    lowered = title.lower()
    return any(keyword in lowered for keyword in KEYWORDS)


def get_relevant_story():
    story_ids = requests.get(TOP_STORIES_URL, timeout=15).json()
    for story_id in story_ids[:MAX_STORIES_TO_CHECK]:
        item = requests.get(ITEM_URL.format(story_id), timeout=15).json()
        title = item.get("title", "")
        if item.get("type") == "story" and matches_keywords(title):
            link = item.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
            discussion = f"https://news.ycombinator.com/item?id={story_id}"
            return {"title": title, "link": link, "discussion": discussion}
    return None


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": False},
        timeout=15,
    )
    resp.raise_for_status()


def main():
    story = get_relevant_story()
    if not story:
        print("No se encontró ninguna noticia relevante hoy.")
        return

    message = (
        f"📰 Noticia del día (IA / programación):\n"
        f"{story['title']}\n"
        f"{story['link']}\n\n"
        f"Discusión: {story['discussion']}"
    )
    send_telegram_message(message)
    print("Noticia enviada.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
