#!/usr/bin/env python3
"""
Write the event's share link into Firestore.

The link is deliberately NOT in this repo: the repo is public, and the whole
point of the Google sign-in on the page is that an unauthenticated stranger
cannot read the URL. It lives in `eventLinks/<event id>` in the hmx-pm-toolbox
project, which `firestore.rules` lets an allowlisted account read and lets
nobody write from a browser.

So this is the way to change it. It writes through the Admin SDK, which
bypasses rules.

    ./tools/set-link.py --url "https://harvestkc.filecloudonline.com/url/..."

Everything else is optional and only changes what the page prints:

    --event-id    which document (default jamf-2026, must match config.js)
    --name        heading, e.g. "JAMF 2026"
    --folder      subheading, e.g. "Presentation Management"
    --path        the footer line

Run with no flags to print what is stored now.
"""
import argparse
import datetime
import os
import sys

import google.auth.transport.requests as gt
from google.oauth2 import service_account

KEY = os.path.expanduser("~/dev/hmx-pm-toolbox-firebase-adminsdk-fbsvc-682edec753.json")
PROJECT = "hmx-pm-toolbox"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
SCOPES = ["https://www.googleapis.com/auth/datastore"]


def session():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    return gt.AuthorizedSession(creds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--event-id", default="jamf-2026")
    ap.add_argument("--url")
    ap.add_argument("--name")
    ap.add_argument("--folder")
    ap.add_argument("--path")
    args = ap.parse_args()

    s = session()
    doc = f"{BASE}/eventLinks/{args.event_id}"

    if not (args.url or args.name or args.folder or args.path):
        r = s.get(doc)
        if r.status_code == 404:
            print(f"eventLinks/{args.event_id}: does not exist")
            return 1
        r.raise_for_status()
        for k, v in sorted(r.json().get("fields", {}).items()):
            print(f"{k:12} {list(v.values())[0]}")
        return 0

    pairs = [
        ("shareUrl", args.url),
        ("eventName", args.name),
        ("folderName", args.folder),
        ("folderPath", args.path),
    ]
    fields = {k: {"stringValue": v} for k, v in pairs if v is not None}

    # updateMask, so a partial call leaves the other fields alone.
    params = [("updateMask.fieldPaths", k) for k in fields]
    params += [("updateMask.fieldPaths", "updatedAt")]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    fields["updatedAt"] = {"timestampValue": now}

    r = s.patch(doc, params=params, json={"fields": fields})
    if not r.ok:
        print(r.status_code, r.text[:500], file=sys.stderr)
        return 1
    print(f"wrote eventLinks/{args.event_id}:")
    for k, v in sorted(r.json().get("fields", {}).items()):
        print(f"  {k:12} {list(v.values())[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
