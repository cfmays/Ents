## Troubleshooting
* gunicorn logs: `sudo journalctl -u entsgunicorn.service`

## Open Questions
* how to properly serve user u0ploaded media. [This page about static files](https://docs.djangoproject.com/en/4.0/howto/static-files/) doesn't seem to tell me, other than to let me know it's going to be a problem
* how to run (e.g.) `python3 manage.py collectstatic` on the server (tried 1st `source`ing `/home/charley/ents.env` and `/home/charley/vents/bin/activate`)


## nginx config
```
server {
    server_name ents.charleymays.org;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/charley/Ents/ents/staticfiles/;
    }


    location = /media/ {
        root /home/charley/ents-media;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/entsgunicorn.sock;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/ents.charleymays.org/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ents.charleymays.org/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = ents.charleymays.org) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name ents.charleymays.org;
    return 404; # managed by Certbot


}
``