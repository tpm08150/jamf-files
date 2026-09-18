# Event Files — JAMF 2026

A one-page launcher for the FileCloud share link, so every machine at the event
has the same easy URL (and can install it as a desktop app).

**Live:** https://tpm08150.github.io/jamf-files/

## Changing the share link

Edit `shareUrl` in [`config.js`](config.js), commit, push. GitHub Pages picks it
up in about a minute. Nothing else in the repo needs to change.

If the link changes mid-event and you can't push, each machine can override it
locally: *Change the share link on this device* on the page itself.

## Regenerating the QR code

The QR points at this page (not at FileCloud), so it keeps working when the
share link changes:

```
npx qrcode -t svg -e M -o qr.svg "https://tpm08150.github.io/jamf-files/" < /dev/null
```

## Notes

- FileCloud sends `X-Frame-Options: SAMEORIGIN`, so the folder cannot be embedded
  in an iframe — the page navigates to it instead.
- `?go=1` skips the page entirely and redirects straight to the folder.
- `?stay=1` overrides a machine's saved "skip this page" setting.
