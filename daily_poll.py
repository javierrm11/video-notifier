import json
import os
from datetime import date

import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_COMMUNITY_CHAT_ID = os.environ["TELEGRAM_COMMUNITY_CHAT_ID"]

BANK_FILE = "polls_bank.json"


def load_bank():
    with open(BANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_today(bank):
    index = date.today().toordinal() % len(bank)
    return bank[index]


def send_poll(poll):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPoll"
    resp = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_COMMUNITY_CHAT_ID,
            "question": poll["question"],
            "options": poll["options"],
            "is_anonymous": True,
        },
        timeout=15,
    )
    resp.raise_for_status()


def main():
    bank = load_bank()
    poll = pick_today(bank)
    send_poll(poll)
    print(f"Encuesta enviada: {poll['question']}")


if __name__ == "__main__":
    main()
