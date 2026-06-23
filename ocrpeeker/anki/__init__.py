import json
import urllib.request
from ocrpeeker import config

ANKI_URL = "http://localhost:8765"


def _request(action: str, **params) -> dict:
    payload = json.dumps({"action": action, "params": params, "version": 6}).encode()
    response = json.load(urllib.request.urlopen(urllib.request.Request(ANKI_URL, payload)))
    if response.get("error"):
        raise RuntimeError(f"AnkiConnect error: {response['error']}")
    return response["result"]


def add_note(sentence: str, translation: str, image_path: str | None = None) -> int:
    deck = config.get(config.ANKI_CONFIG, "deck")
    model = config.get(config.ANKI_CONFIG, "model")
    tags = config.get(config.ANKI_CONFIG, "tags").split()
    fields = {"Sentence": sentence, "Translation": translation}
    note = {"deckName": deck, "modelName": model, "fields": fields, "tags": tags}
    if image_path:
        note["picture"] = [{"path": image_path, "filename": "ocrpeeker.png", "fields": ["Image"]}]
    return _request("addNote", note=note)
