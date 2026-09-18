# Event Files

A one-page launcher for an event's FileCloud share folder, behind the same
Google sign-in the Hub uses, so every machine at the event has one easy URL
(and can install it as a desktop app).

**Live:** https://tpm08150.github.io/jamf-files/

## How the security actually works

This repo is public and the page is a static file with no server behind it, so
none of the gating can live here.

- The share URL is in Firestore at `eventLinks/<eventId>` in the
  `hmx-pm-toolbox` project. **It is not in this repo.**
- `firestore.rules` lets `isStaff() || isContractor()` read that collection —
  anyone on the Hub's allowlist, contractors included — and lets nobody write
  it from a browser.
- The page signs in with Google, reads the document, and only then has a URL to
  put on the button.

So the rule is the boundary and the page is a courtesy layer. Widening that one
rule publishes the link; there is no second gate.

What this does **not** do: once an allowed person opens the folder, the FileCloud
URL is in their address bar, and FileCloud treats anyone holding it as welcome —
including to upload. If the URL gets forwarded, the sign-in here does nothing
about it. The control for that is in FileCloud (share password, expiry, or a new
link), not in this app.

## Changing the share link

Never in this repo — write it to Firestore:

```bash
./tools/set-link.py --url "https://harvestkc.filecloudonline.com/url/..."
```

It takes effect on every machine at the next page load, no deploy. Run it with
no flags to print what's stored. `--name`, `--folder` and `--path` change the
labels the page prints; `--event-id` picks a different event document.

## Running it for a different event

1. `./tools/set-link.py --event-id someevent-2027 --url "..." --name "..."`
2. Change `eventId` in [`config.js`](config.js) to match, and regenerate the QR.
3. Push.

## After changing the rules

`firestore.rules` lives in `~/dev/firebase-rules/hmx-pm-toolbox/` and is
published by pasting into the Firebase console. Afterwards:

```bash
cd ~/dev/firebase-rules && ./rules.py check
```

then, from this repo, ask Firestore for the link with no credentials at all and
confirm it refuses:

```bash
./tools/attack-link-rule.py
```

⚠️ That script is only meaningful **after** publishing. Against a ruleset with
no `eventLinks` block every refusal check passes too, because Firestore's
default is deny — which reads as "airtight" rather than "not there". Its last
check is an admin read that proves the document exists to be leaked.

## Firebase console, once per hosting domain

**Authentication → Settings → Authorized domains** must contain
`tpm08150.github.io`, or the sign-in popup is rejected.

## Regenerating the QR code

The QR points at this page, not at FileCloud, so it survives a link change:

```bash
npx qrcode -t svg -e M -o qr.svg "https://tpm08150.github.io/jamf-files/" < /dev/null
```

(The `< /dev/null` matters — the CLI otherwise waits on stdin and looks hung.)

## Notes

- FileCloud sends `X-Frame-Options: SAMEORIGIN`, so the folder cannot be
  embedded in an iframe. The page navigates to it instead.
- `?go=1` skips the page and redirects as soon as the link loads.
  `?stay=1` overrides a machine's saved "skip this page" setting.
- Firestore's on-disk cache is on, so a machine that has loaded the link once
  can still get to the folder with the page offline.
