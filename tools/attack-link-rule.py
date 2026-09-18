#!/usr/bin/env python3
"""
Attack the eventLinks rule from outside the browser.

The page is a public static file on GitHub Pages. Its Google sign-in is a
courtesy layer — a stranger can read index.html, config.js and the Firebase
project id in about ten seconds, and then ask Firestore directly. The only
thing between them and the share URL is the rule. So ask Firestore directly,
with **no credentials but the public web API key**, and see what it hands over.

Copied from presentation-manager/rules/attack-rooms-rule.py, which is where the
shape came from.

⚠️ **Run this after publishing the ruleset, not before.** Against a ruleset with
no eventLinks block every refusal check passes — Firestore's default is deny —
which reads as "the rule is airtight" rather than "the rule is not there". The
admin control at the end is what tells the two apart: it proves the document is
really there to be leaked.

Read-only. Nothing is written, and the one write probe is expected to bounce.
"""
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

import google.auth.transport.requests as gt
from google.oauth2 import service_account

PROJECT = "hmx-pm-toolbox"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
EVENT_ID = sys.argv[1] if len(sys.argv) > 1 else "jamf-2026"

HERE = os.path.dirname(os.path.abspath(__file__))


def web_api_key():
    """Read the key from the page's own config rather than keeping a copy."""
    path = os.path.join(HERE, "..", "config.js")
    m = re.search(r'apiKey:\s*"([^"]+)"', open(path, encoding="utf-8").read())
    if not m:
        sys.exit(f"couldn't find apiKey in {path}")
    return m.group(1)


API_KEY = web_api_key()
results = []


def anon(method, path, body=None):
    """A request with no identity at all — only the public web API key."""
    sep = "" if path.startswith(":") else "/"
    url = f"{BASE}{sep}{path}{'&' if '?' in path else '?'}key={API_KEY}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or "{}")


def admin():
    keys = glob.glob(os.path.expanduser("~/dev/hmx-pm-toolbox-firebase-adminsdk-*.json"))
    if not keys:
        sys.exit("service-account key not found in ~/dev/")
    creds = service_account.Credentials.from_service_account_file(
        keys[0], scopes=["https://www.googleapis.com/auth/datastore"])
    return gt.AuthorizedSession(creds)


def check(name, ok, detail=""):
    results.append((name, ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))


def denied(status, body):
    """403 with a rules refusal, not a 400 that failed for some other reason."""
    return status == 403 and "PERMISSION_DENIED" in json.dumps(body)


def leaked(body):
    """Did a response actually carry the share URL?"""
    return "filecloudonline.com" in json.dumps(body)


def main():
    print(f"anonymous probes against eventLinks/{EVENT_ID}\n")

    st, body = anon("GET", f"eventLinks/{EVENT_ID}")
    check("get the document", denied(st, body), f"HTTP {st}")
    check("and it did not carry the URL", not leaked(body))

    st, body = anon("GET", "eventLinks?pageSize=50")
    check("list the collection", denied(st, body), f"HTTP {st}")
    check("and the listing did not carry the URL", not leaked(body))

    # A document that does not exist. If this 404s instead of 403ing, the rule
    # is answering "no such document" to strangers, which is a slower leak but
    # still a leak: it tells them which event ids are real.
    st, body = anon("GET", "eventLinks/zzTESTdeleteMEnoSuchEvent")
    check("get a non-existent document", denied(st, body), f"HTTP {st}")

    # Nobody writes this from a browser, not even an allowlisted one.
    st, body = anon("POST", ":commit", {"writes": [{
        "update": {
            "name": f"projects/{PROJECT}/databases/(default)/documents/eventLinks/{EVENT_ID}",
            "fields": {"shareUrl": {"stringValue": "https://example.invalid/hijacked"}},
        }
    }]})
    check("overwrite the share URL", denied(st, body), f"HTTP {st}")

    # The allowlist is how the rule decides. Reading it needs auth too.
    st, body = anon("GET", "allowlist?pageSize=5")
    check("read the allowlist", denied(st, body), f"HTTP {st}")

    # Control: the document is really there. Without this, every check above
    # passes just as well against a typo'd collection name.
    r = admin().get(f"{BASE}/eventLinks/{EVENT_ID}")
    have = r.ok and "shareUrl" in r.json().get("fields", {})
    check("control: the document exists and has a shareUrl (admin)", have, f"HTTP {r.status_code}")

    bad = [n for n, ok in results if not ok]
    print()
    if bad:
        print(f"{len(bad)} of {len(results)} checks FAILED")
        return 1
    print(f"all {len(results)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
