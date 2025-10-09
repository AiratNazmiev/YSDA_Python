import json
import requests
import time
import sys
import os
import re

from dotenv import load_dotenv  # will not work on your machine unless downloaded by pip

load_dotenv()

BOT_SECRET = os.getenv("BOT_SECRET")

def _parse_chat_ids(raw):
    if not raw:
        return []
    # Split by commas, semicolons, or whitespace; preserve duplicates
    parts = re.split(r"[\s,;]+", raw)
    return [p for p in parts if p]

# Prefer CHAT_IDS, fallback to CHAT_ID for backward compatibility
_CHAT_IDS_RAW = os.getenv("CHAT_IDS") or os.getenv("CHAT_ID")
CHAT_IDS = _parse_chat_ids(_CHAT_IDS_RAW)

DRY_RUN = not (BOT_SECRET and CHAT_IDS)
# pyrefly: ignore  # unsupported-operation
LINK = None if DRY_RUN else ("https://api.telegram.org/bot" + BOT_SECRET + "/sendMessage")

MAX_SENDING_ATTEMPTS = 5

def send(message="Sample text."):
    if DRY_RUN:
        if CHAT_IDS:
            for _chat_id in CHAT_IDS:
                print(f"[DRY RUN] [{_chat_id}] {message}", file=sys.stderr)
        else:
            print(f"[DRY RUN] {message}", file=sys.stderr)
        return

    for _chat_id in CHAT_IDS:
        message_data = {"chat_id": _chat_id, "text": message}

        sent_successfully = False
        attempts = 0
        while not sent_successfully and attempts < MAX_SENDING_ATTEMPTS:
            try:
                r1 = requests.get(LINK, params=message_data)
                sent_successfully = json.loads(r1.text)["ok"]
            except Exception:
                pass
            if not sent_successfully:
                time.sleep(2**attempts)
                attempts += 1
        if not sent_successfully:
            sys.stderr.write("Can't send to {}:\n{}".format(_chat_id, message))
