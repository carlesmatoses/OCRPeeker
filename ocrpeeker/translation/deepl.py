import time
import requests


def translate(text: str, source: str, target: str) -> str:
    text = text[:140] if len(text) > 140 else text
    response = requests.post(
        "https://www2.deepl.com/jsonrpc",
        json={
            "jsonrpc": "2.0",
            "method": "LMT_handle_jobs",
            "params": {
                "jobs": [{
                    "kind": "default",
                    "raw_en_sentence": text,
                    "raw_en_context_before": [],
                    "raw_en_context_after": [],
                    "preferred_num_beams": 4,
                    "quality": "fast",
                }],
                "lang": {
                    "user_preferred_langs": [target.upper()],
                    "source_lang_user_selected": source.upper(),
                    "target_lang": target.upper(),
                },
                "priority": -1,
                "commonJobParams": {},
                "timestamp": int(round(time.time() * 1000)),
            },
            "id": 40890008,
        },
    )
    output = response.json()
    if "result" in output:
        return output["result"]["translations"][0]["beams"][0]["postprocessed_sentence"]
    if "error" in output:
        return f"Error: {output['error']['message']}"
    return "Translation failed"
