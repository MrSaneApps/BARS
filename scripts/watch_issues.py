#!/usr/bin/env python3
"""
Poll GitHub Issues on veg/BARS for open issues labeled 'pending-review'
(or with title starting with '[Review]'). Outputs JSON list of pending review requests.
"""

import json
import subprocess
import sys

REPO = "veg/BARS"


def fetch_pending_issues() -> list[dict]:
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        REPO,
        "--state",
        "open",
        "--limit",
        "1000",
        "--json",
        "number,title,body,labels,createdAt,url",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(f"Error querying GitHub issues: {res.stderr}\n")
        sys.exit(res.returncode)

    issues = json.loads(res.stdout)
    pending = []
    for iss in issues:
        label_names = {lbl.get("name", "").lower() for lbl in iss.get("labels", [])}
        if "reviewed" in label_names:
            continue
        if "pending-review" in label_names or iss.get("title", "").strip().lower().startswith("[review]"):
            pending.append(iss)
    return pending


if __name__ == "__main__":
    pending_issues = fetch_pending_issues()
    print(json.dumps(pending_issues, indent=2))
