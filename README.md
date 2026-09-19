# Event Files — the web page

One easy link to an event's FileCloud shared folder, behind the same Google
sign-in the Harvest Hub uses, and the place people download the Mac app from.

**Live:** https://tpm08150.github.io/jamf-files/

The Mac app that actually keeps machines in sync is a separate, **private** repo
— `tpm08150/event-files-app` — because it carries credentials this one must not.
This page is the front door; the app is the thing rooms depend on.

---

## How the security works

⚠️ **This repo is public and the page is a static file with no server**, so none
of the gating can live here. Everything on the page that matters comes from
Firestore after sign-in:

| In Firestore | Not in this repo |
|---|---|
| `eventLinks/<eventId>.shareUrl` | the FileCloud share link |
| `eventLinks/<eventId>.appUrl` | where to download the Mac app |

`firestore.rules` lets `isStaff() || isContractor()` read that collection —
anyone on the Hub's allowlist, contractors included — and lets nobody write it
from a browser. **That rule is the boundary and the page is a courtesy layer.**
Widen it and the link is public; there is no second gate.

⚠️ **What it does not do:** once an allowed person opens the folder, the
FileCloud URL is in their address bar, and FileCloud welcomes anyone holding it
— including to upload. A forwarded URL walks straight past this sign-in. The
control for that lives in FileCloud (share password, expiry, or a new link).

⚠️ **The original share link is still in this repo's first commit** (`f65a90a`),
from before the sign-in existed. Knowingly kept. Do not read the sign-in as
protecting a secret that is already out; it protects *discovery*.

---

## Changing what the page shows

Never by editing this repo — write to Firestore:

```bash
./tools/set-link.py --url "https://harvestkc.filecloudonline.com/url/..."   # the folder
./tools/set-link.py --name "JNUC" --folder "Presentation Management"        # what it prints
./tools/set-link.py --app "https://firebasestorage.googleapis.com/..."      # the app download
```

Run it with no flags to print what is stored. Changes take effect on the next
page load — no deploy.

⚠️ `--app` is as sensitive as the share link: the build it points at has the
link inside it. It lives in the same gated document and the page hands it out
only to a signed-in, allowlisted account.

---

## One-time setup, and the thing that will catch you

⚠️ **Every hosting domain must be in Firebase → Authentication → Settings →
Authorized domains.** Without it, Google refuses the popup *before* the account
picker opens, and the page shows `auth/unauthorized-domain`. It looks like the
app rejected somebody when in fact it never asked. `tpm08150.github.io` was
missing for a day for exactly this reason; the page now says so in words rather
than printing the code.

⚠️ **A downloaded app is quarantined.** The builds are ad-hoc signed, not signed
with a paid Apple certificate, so macOS says *"Apple could not verify Event
Files is free of malware"* with **Move to Trash** as the default button. The page
says this above the download, un-collapsed, because it has to be read *before*
the click. A copy handed over on a flash drive skips all of it — quarantine comes
from the browser.

---

## After changing the rules

`firestore.rules` lives in `~/dev/firebase-rules/hmx-pm-toolbox/` and is
published by pasting into the Firebase console. Afterwards:

```bash
cd ~/dev/firebase-rules && ./rules.py check
./tools/attack-link-rule.py
```

The probe asks Firestore for the link with **no credentials at all** and
confirms it refuses. ⚠️ It is only meaningful *after* publishing: against a
ruleset with no `eventLinks` block every refusal passes too, because Firestore's
default is deny. Its last check is an admin read proving the document exists to
be leaked.

---

## Regenerating the QR code

It points at this page, not at FileCloud, so it survives a link change:

```bash
npx qrcode -t svg -e M -o qr.svg "https://tpm08150.github.io/jamf-files/" < /dev/null
```

(The `< /dev/null` matters — the CLI otherwise waits on stdin and looks hung.)

---

## Notes

- FileCloud sends `X-Frame-Options: SAMEORIGIN`, so the folder cannot be
  embedded. The page navigates to it.
- `?go=1` skips the page and redirects once the link loads; `?stay=1` overrides
  a machine's saved "skip this page" setting.
- The page is a PWA — installable from Chrome, Edge or Safari's *Add to Dock* —
  and its service worker is network-first, so a pushed change is picked up
  rather than served stale from cache.
