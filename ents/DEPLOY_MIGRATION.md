# One-time migration: deploying the zoo app + swapping in the dev database

This is a **one-time runbook**, not the routine deploy process (that's still in
`README.md`). It does two things the routine process never does:

1. Deploys the new code (the whole `zoo` app: calendars, training log,
   Manage Items/Calendars/Training, etc.) on top of the currently-running
   simple Ents app.
2. Replaces the server's real database and photo files with the dev copy
   built during this project (1,420 catalog items, 958 with photos, 111
   calendars, ~199 training animals) — **discarding the server's current
   catalog and its 4 accounts' passwords** in favor of the dev copy.

Read the whole thing once before running anything. Steps marked **⚠️
DESTRUCTIVE** overwrite real files with no code-level undo — the backup steps
before them are not optional.

`main` is already merged and pushed (commit `2099824`) — this file assumes
you're deploying that.

---

## 0. Before you start

- **Take a DigitalOcean snapshot of the droplet right now**, before anything
  else. That's your real undo button if something goes wrong in a way the
  file backups below don't cover. This is a few minutes in the DO control
  panel, not something done over SSH.
- Expect a few minutes of downtime for the app around step 4 (stopping/
  restarting gunicorn). With 4 real users this should be a non-issue, but
  pick a moment that isn't disruptive.
- You'll need `Enrichment Calendars v4.xlsx`, `Aquarium Enrichment Calendars
  V4.xlsx`, `Animal Behavior Master List .pdf`, and the `enrichments/` photo
  folder **only if you ever want to re-run an import command on the
  server** — the swap in this runbook doesn't need them, since dev's
  database and media are being copied over wholesale, already built.

## 1. Resolve the env-file question first

`README.md`'s own "Open Questions" section flags that it was never settled
whether the server actually reads `/home/charley/ents.env` (sourced by hand
before running commands) or `ents/.env` in the project directory (which is
what `settings.py` actually loads via `django-environ`). **Don't guess —
check both on the server:**

```
cat /home/charley/ents.env
cat /home/charley/Ents/ents/.env
```

Whichever one has the real `SECRET_KEY` / `ENTS_ALLOWED_HOSTS` /
`ENTS_MEDIA_ROOT` values is the one that matters. If both exist and differ,
stop and figure out which one `settings.py` is actually picking up (e.g. by
checking `python3 manage.py diffsettings` while it's running, or by
temporarily changing one value and seeing if it takes effect) before
touching anything else. Note the value of `ENTS_MEDIA_ROOT` — you'll need it
in step 5.

## 2. Back up what's currently live

On the server, in the app directory:

```
cd /home/charley/Ents/ents
mkdir -p ~/ents-backups
cp db.sqlite3 ~/ents-backups/db.sqlite3.$(date +%Y%m%d-%H%M%S)
tar czf ~/ents-backups/media.$(date +%Y%m%d-%H%M%S).tar.gz media/
```

Confirm both files landed in `~/ents-backups/` and aren't empty before
continuing.

## 3. Deploy the code

Same shape as the routine workflow in `README.md`:

```
cd /home/charley/Ents
git pull
cd ents
source /home/charley/vents/bin/activate
pip install -r requirements.txt
```

Note: `requirements.txt` is a straight `pip freeze` of the local dev
environment, so it includes some dev-only tools that don't do anything
useful in production (`ipdb`, `ipython`, `jedi`, `prompt-toolkit`, and a
handful of their dependencies). Harmless to install, just not needed — not
worth hand-editing the file over.

**Do not run `migrate` yet** — that comes after the database swap in step 5,
where it doubles as a verification step.

## 4. Stop the app

```
sudo systemctl stop entsgunicorn.service
```

## 5. ⚠️ DESTRUCTIVE: swap in the dev database and photos

From your Mac, copy the dev database and the dev media folder to the server.
Adjust the destination path to wherever you confirmed `ENTS_MEDIA_ROOT`
points in step 1 — the example below assumes it's `media/enrichments` inside
the project directory, same as dev.

**Important distinction:** there are two different `enrichments` folders on
your Mac. You want `ents/media/enrichments/` (the app's actual photo
storage, ~97 MB, 958 files) — **not** the `enrichments/` folder at the repo
root next to it, which is the raw source folder used only by the temporary
"Unassigned photos" section and isn't part of the deployed app.

From `/Users/charlesmays/Dev/Ents/ents`:

```
scp db.sqlite3 charley@<droplet-ip>:/home/charley/Ents/ents/db.sqlite3
rsync -av media/enrichments/ charley@<droplet-ip>:/home/charley/Ents/ents/media/enrichments/
```

(`rsync` rather than `scp -r` so it's resumable if the connection drops
partway through — 97 MB shouldn't take long, but no reason not to.)

Back on the server:

```
cd /home/charley/Ents/ents
source /home/charley/vents/bin/activate
python3 manage.py migrate
```

**`migrate` should print "No migrations to apply."** Dev's database is
already fully migrated, so this is really a sanity check: if it instead
tries to apply migrations, stop — that means the code you deployed doesn't
match the migration state of the database you just copied over, and
something is inconsistent. Don't proceed until you understand why.

```
python3 manage.py collectstatic
```

## 6. Set real passwords before restarting

Dev's database has the copied-over `charley` / `carolyn` / `megan` /
`sarahh` accounts, but most passwords in dev (including these) are the
shared placeholder `1957` used throughout the import from the spreadsheet.
Set real ones now, before the site is reachable again, rather than leaving
a known shared password live even briefly:

```
python3 manage.py changepassword charley
python3 manage.py changepassword carolyn
python3 manage.py changepassword megan
python3 manage.py changepassword sarahh
```

(`changepassword` works for any account regardless of role, no web login
needed.) Set something you'll actually give each person, or a throwaway
temporary one and have them use the app's own "Change password" page — in
the menu bar once logged in — to set their real one.

**One thing worth deciding, not urgent:** in dev, only `charley` is a
Django-admin ("staff") user; `carolyn` is a Supervisor (full access to
Manage Items/Calendars/Training/Item Assignments — the new custom pages
that replace most of what admin access used to be for), and `megan` /
`sarahh` are plain keepers (scoped to whichever Strings they're assigned
to). In the old app all four had Django-admin access. If you want Megan or
Sarah to have Supervisor-level capability like they had admin access
before, that's a Manage Training Logs / Django admin change you can make
any time after this deploy — it doesn't need to happen now.

## 7. Restart and verify

```
sudo systemctl restart entsgunicorn.service
sudo systemctl status entsgunicorn.service
```

Then in a browser:

- Load the site. Confirm the homepage (Enrichment Items) renders and shows
  item thumbnails — if thumbnails are broken but everything else works,
  that's almost always the nginx media alias
  (`/etc/nginx/sites-available/ents.charleymays.org`) still pointing at the
  old media path rather than wherever you put `media/enrichments/` in
  step 5.
- Log in as `charley`.
- Open Enrichment Calendars, open a calendar (e.g. Tiger), confirm it loads
  with its items and animal choices.
- Open Manage Training Logs, confirm strings/keepers/animals show up.
- Check `sudo journalctl -u entsgunicorn.service` for errors if anything
  looks wrong.

## If something's badly wrong: rollback

```
sudo systemctl stop entsgunicorn.service
cd /home/charley/Ents/ents
cp ~/ents-backups/db.sqlite3.<timestamp> db.sqlite3
rm -rf media/enrichments
tar xzf ~/ents-backups/media.<timestamp>.tar.gz
sudo systemctl start entsgunicorn.service
```

That restores exactly what was running before step 4. If even that doesn't
fix it, restore the DigitalOcean snapshot from step 0.

---

## Ask me for help if:

- Step 1 turns up something unexpected about the env files.
- `migrate` in step 5 wants to apply migrations instead of saying "No
  migrations to apply."
- Anything in `journalctl -u entsgunicorn.service` after step 7 doesn't make
  sense.
- You want help deciding Megan/Sarah's roles in step 6.

I don't have access to the droplet, so I can only help by reading whatever
output you paste back here.
