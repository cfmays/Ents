## Troubleshooting
* gunicorn logs: `sudo journalctl -u entsgunicorn.service`

## Open Questions

* what image file type should I save in the db? png   check for file size differences

* how to run (e.g.) `python3 manage.py collectstatic` on the server (tried 1st `source`ing `/home/charley/ents.env` and `/home/charley/vents/bin/activate`)
    * likely this will be solved by the env package, but also changing the `/home/charley/ents.env` file to say `export` at the beginnign would work?


## nginx 
* config `/etc/nginx/sites-available/ents.charleymays.org`
* logs `/var/log/nginx`
    * list dir with most recent at the bottom: `ls -lrt` 

## workflow
1. work locally
    1. if new requirements, do PIP freeze and install on the server also
1. test changes locally
    1. `python3 manage.py collectstatic`
    1. `python3 manage.py migrate`
    1. restart django dev server (kill it then, `python3 manage.py runserver`)
1. commit your changes and sync to repo
    1. `git status`
    1. `git add <whatever files>`
    1. `git commit -m'<descriptive message>'`
    1. `git push`
1. on the (remote) server
    1. get changes from repo
        1. `cd /home/charley/Ents/ents`
        1. `git pull`
    1. deploy changes
        1. `source /home/charley/vents/bin/activate`
        1. `python3 manage.py collectstatic`
        1. `python3 manage.py migrate`
        1. `sudo systemctl restart entsgunicorn.service`
    1. check django service status
        1. `sudo systemctl status entsgunicorn.service`
    1. test changes on server
