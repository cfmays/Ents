# Deploying Ents to the DigitalOcean droplet

Follow these steps every time you deploy new code to the Ubuntu server.
Everything after step 1 is run on the server over SSH.

## Where things are on the server

| What | Where |
|---|---|
| Code (git repo) | `/home/charley/Ents` |
| Django project (where `manage.py` is) | `/home/charley/Ents/ents` |
| Python virtual environment | `/home/charley/vents` |
| Settings file (`SECRET_KEY`, `DEBUG`, `ENTS_ALLOWED_HOSTS`, `ENTS_MEDIA_ROOT`) | `/home/charley/Ents/ents/.env` |
| Database | `/home/charley/Ents/ents/db.sqlite3` |
| Uploaded item photos | `/home/charley/ents-media/enrichments/` |
| Static files (made by `collectstatic`) | `/home/charley/Ents/ents/staticfiles/` |
| App server | `entsgunicorn.service`, started by `entsgunicorn.socket` |
| Web server config | `/etc/nginx/sites-available/ents.charleymays.org` |
| Web server logs | `/var/log/nginx/` |
| Backups (made in step 3) | `/home/charley/ents-backups/` |

The database, `.env` and photos are **not** in git. `git pull` never changes them.

---

## 1. On your Mac: test, commit and push

From `/Users/charlesmays/Dev/Ents/ents`:

```
.venv/bin/python manage.py test
.venv/bin/python manage.py makemigrations --check --dry-run
```

The tests should end with `OK`. The second command should say
`No changes detected`. If it doesn't, you changed a model without making a
migration: run `.venv/bin/python manage.py makemigrations` and commit the new
file in `migrations/`.

If you added a Python package, update `requirements.txt`:

```
.venv/bin/pip freeze > requirements.txt
```

Then commit and push:

```
git status
git add <the files you changed>
git commit -m "<what changed>"
git push
```

## 2. Log in to the server and activate the virtual environment

```
ssh charley@<droplet-ip>
cd /home/charley/Ents/ents
source /home/charley/vents/bin/activate
```

The `source` line activates the virtual environment. The prompt should now
start with `(vents)`. Without it, `python3 manage.py ...` fails with
`No module named 'django'` or `No module named 'environ'`.

Run the rest of the steps from this same terminal. If you open a new one, run
these three lines again first.

## 3. Back up the database and photos

Do this every time, even for a small change.

```
mkdir -p ~/ents-backups
cp db.sqlite3 ~/ents-backups/db.sqlite3.$(date +%Y%m%d-%H%M%S)
tar czf ~/ents-backups/media.$(date +%Y%m%d-%H%M%S).tar.gz -C /home/charley/ents-media enrichments/
ls -lh ~/ents-backups | tail -4
```

Check that the new files are listed and aren't 0 bytes.

Old backups pile up, so now and then delete the old ones:
`ls -lt ~/ents-backups` lists the newest first.

## 4. Get the new code

First make sure you're in the venv; see step 2

```
cd /home/charley/Ents
git pull
cd ents
```

If `git pull` complains about local changes, don't force it. Run `git status`
to see what was changed on the server and sort that out first.

## 5. Install packages (only if `requirements.txt` changed)

`git pull` lists the files that changed. If `requirements.txt` is one of them:

```
pip install -r requirements.txt
```

## 6. Update the database and static files

```
python3 manage.py migrate
python3 manage.py collectstatic --noinput
```

`migrate` either applies the new migrations or says
`No migrations to apply.` Both are fine. If it shows an error, stop and go to
"Rolling back" below.

## 7. Restart the app

```
sudo systemctl restart entsgunicorn.service
sudo systemctl status entsgunicorn.service --no-pager
```

The status should say `active (running)`. Press `q` if it doesn't return to the
prompt.

Only if you changed the nginx config:

```
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Check it in a browser

- The home page loads and the item thumbnails show.
- You can log in.
- Open a calendar and check that its items and animals are listed.
- Try out whatever you just changed.

If something is wrong, look at the error messages:

```
sudo journalctl -u entsgunicorn.service -n 100 --no-pager
sudo tail -n 50 /var/log/nginx/error.log
```

Common problems:
- **The page says "Bad Request (400)":** the site's address is missing from
  `ENTS_ALLOWED_HOSTS` in `.env`.
- **"502 Bad Gateway":** gunicorn isn't running. Check the `journalctl` output
  above. Often it's a Python error in the new code.
- **Pages work but there are no photos:** the `/media/` location in the nginx
  config doesn't point to `/home/charley/ents-media/`.
- **Pages have no styling:** `collectstatic` wasn't run, or the `/static/`
  location in the nginx config doesn't point to `staticfiles/`.

---

## Rolling back

Use this if the new version is broken and you can't fix it quickly.
If you're in a new terminal, run the three lines from step 2 first.

1. Go back to the code that was running before. `git log --oneline -5` shows
   the recent commits; pick the one before your deploy:

   ```
   cd /home/charley/Ents
   git log --oneline -5
   git checkout <previous-commit-id>
   cd ents
   ```

2. If `migrate` in step 6 applied migrations, put the database back from the
   backup you made in step 3:

   ```
   sudo systemctl stop entsgunicorn.socket entsgunicorn.service
   cp ~/ents-backups/db.sqlite3.<timestamp> db.sqlite3
   sudo systemctl start entsgunicorn.socket entsgunicorn.service
   ```

   Anything people entered since the backup is lost, so do this soon after
   the deploy.

3. Restart and check:

   ```
   python3 manage.py collectstatic --noinput
   sudo systemctl restart entsgunicorn.service
   ```

When the fix is pushed, go back to the normal branch before deploying again:

```
cd /home/charley/Ents
git checkout main
git pull
```

To restore the photos as well (rarely needed):

```
rm -rf /home/charley/ents-media/enrichments
tar xzf ~/ents-backups/media.<timestamp>.tar.gz -C /home/charley/ents-media
```

If nothing else works, restore a DigitalOcean snapshot of the droplet from the
DO control panel. Taking a snapshot before a big change is a good habit.

---

## Other handy commands on the server

Run these after the three lines from step 2 (so the prompt starts with `(vents)`).

| Task | Command |
|---|---|
| Reset someone's password | `python3 manage.py changepassword <username>` |
| Make a new admin account | `python3 manage.py createsuperuser` |
| Copy the live database to your Mac (run on the Mac) | `scp charley@<droplet-ip>:/home/charley/Ents/ents/db.sqlite3 ~/Desktop/prod-db.sqlite3` |
