"""Prints one line whenever the reviewer's notes change (reads annotations.json every 2 seconds).

    python eval/error_discovery/watch.py
"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_discovery_data", "annotations.json")


def snapshot():
    try:
        with open(PATH, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def parse(text):
    try:
        d = json.loads(text or "{}")
    except ValueError:
        return None
    return {a["id"]: a for a in d.get("annotations", [])}, d.get("reviewed", {})


last = snapshot()
while True:
    time.sleep(2)
    cur = snapshot()
    if cur is None or cur == last:
        continue
    old, new = parse(last), parse(cur)
    if new is None:
        continue  # caught mid-write; the next read sees the whole file
    old_notes, old_rev = old if old else ({}, {})
    notes, reviewed = new
    parts = [f"{len(notes)} notes, {len(reviewed)} records marked reviewed"]
    for i, a in notes.items():
        if i not in old_notes:
            parts.append(f'+ {a["record_id"]} [{a["block"]}] "{a["text"][:70]}" -> {a["note"][:160]}')
        elif a.get("note") != old_notes[i].get("note"):
            parts.append(f'~ {a["record_id"]} -> {a["note"][:160]}')
    gone = [i for i in old_notes if i not in notes]
    if gone:
        parts.append(f"- {len(gone)} removed")
    newly = [r for r in reviewed if r not in old_rev]
    if newly:
        parts.append("reviewed: " + ", ".join(newly))
    print(" | ".join(parts), flush=True)
    last = cur
