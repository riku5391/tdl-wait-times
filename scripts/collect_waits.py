#!/usr/bin/env python3
import datetime as dt
import json
import os
import pathlib
import urllib.request

PARK = "3cc919f1-d16d-43e0-8c3f-1dd269bd1a42"
DEST = pathlib.Path("data/wait-history.json")

def main():
    url = f"https://api.themeparks.wiki/v1/entity/{PARK}/live"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TDLPersonalWaitCollector/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)

    entries = payload.get("liveData")
    if not isinstance(entries, list):
        raise ValueError("liveData missing")

    timestamp = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    rows = []

    for item in entries:
        if item.get("entityType") != "ATTRACTION":
            continue
        if item.get("status") != "OPERATING":
            continue

        queue = item.get("queue") or {}
        standby = queue.get("STANDBY") or {}
        wait = standby.get("waitTime")

        if isinstance(wait, bool) or not isinstance(wait, (int, float)):
            continue
        if not 0 <= wait <= 600 or not item.get("id"):
            continue

        rows.append({
            "t": timestamp,
            "id": str(item["id"]),
            "name": str(item.get("name") or "名称不明"),
            "wait": wait,
        })

    if not rows:
        print("No valid observations; keeping history")
        return

    if DEST.exists():
        history = json.loads(DEST.read_text(encoding="utf-8"))
    else:
        history = []

    if not isinstance(history, list):
        raise ValueError("Invalid history")

    cutoff = timestamp - 90 * 86400000
    history = [
        row for row in history
        if isinstance(row, dict)
        and isinstance(row.get("t"), (int, float))
        and row["t"] >= cutoff
    ]

    keys = {(row.get("t"), row.get("id")) for row in history}
    for row in rows:
        key = (row["t"], row["id"])
        if key not in keys:
            history.append(row)
            keys.add(key)

    DEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEST.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(history, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, DEST)

    print(f"Collected {len(rows)} attractions; total {len(history)} observations")

if __name__ == "__main__":
    main()
