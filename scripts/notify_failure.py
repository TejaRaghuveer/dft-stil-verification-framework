#!/usr/bin/env python3
"""Send failure notifications to Slack/Teams webhooks."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request


def _post_json(url: str, payload: dict) -> None:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10):
        return


def main() -> int:
    ap = argparse.ArgumentParser(description="Send CI failure notifications.")
    ap.add_argument("--channel", action="append", choices=["slack", "teams"], default=[])
    ap.add_argument("--context", default="ci")
    args = ap.parse_args()

    repo = os.getenv("GITHUB_REPOSITORY", "unknown/repo")
    run_id = os.getenv("GITHUB_RUN_ID", "unknown")
    branch = os.getenv("GITHUB_REF_NAME", "unknown")
    text = f"[{args.context}] CI failure in {repo} on branch {branch}. Run: https://github.com/{repo}/actions/runs/{run_id}"

    for channel in args.channel:
        if channel == "slack":
            url = os.getenv("SLACK_WEBHOOK_URL", "")
            if url:
                _post_json(url, {"text": text})
        if channel == "teams":
            url = os.getenv("TEAMS_WEBHOOK_URL", "")
            if url:
                _post_json(url, {"text": text})
    print("Notification dispatch completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
