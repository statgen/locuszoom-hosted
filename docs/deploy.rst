Deploy
========
Create two config files describing the production environment and populate secrets, config variables, etc as appropriate:
`.envs/.production`


Make sure to build the UI code (`yarn install && yarn run prod`) before creating the docker container. (in the future this step should be automated!!)

On the host system, create a folder `/var/lz-uploads`. This will be mounted as a volume where all user-uploaded GWAS
files will be stored.

Build the docker container in production (or download an apropriate premade image):
`sudo docker-compose -f production.yml build`

Start the container:
`sudo docker-compose -f production.yml up -d`

Apply migrations to create an initial working version of the app:
`sudo docker-compose -f production.yml run --rm django python manage.py migrate`

This demo app runs collectstatic and uses whitenoise to serve automatically without a further build/deploy step.

The service will be deployed initially as an apache reverse proxy to a docker container. Mod proxy must be enabled:
`sudo a2enmod proxy_http`

Apache configuration must be updated, adding an SSL virtual host specifying a proxy to the process, which will run in a docker container.

(make sure to update `ServerName` for your use case, and create a new SSL cert using Certbot/LetsEncrypt!)

```
<IfModule mod_ssl.c>
    <VirtualHost *:443>
        ServerName locuszoom.occsci.com

        # strip the X-Forwarded-Proto header from incoming requests
        RequestHeader unset X-Forwarded-Proto

        # set the header for requests using HTTPS
        RequestHeader set X-Forwarded-Proto https env=HTTPS

        ProxyPass / http://localhost:5000/ keepalive=On
        ProxyPassReverse / http://localhost:5000/

        # TODO: In production, put this behind UM VPNs only
        ProxyPass /celery-flower http://localhost:5555/ keepalive=On
        ProxyPassReverse /celery-flower/ http://localhost:5555/

        # Logging configuration
        LogLevel warn
        ErrorLog ${APACHE_LOG_DIR}/error_lzoccsci.log
        CustomLog ${APACHE_LOG_DIR}/ssl_access_lzoccsci.log combined

        # TODO: SSL CONFIGURATION GOES HERE
SSLCertificateFile /etc/letsencrypt/live/locuszoom.occsci.com/fullchain.pem
SSLCertificateKeyFile /etc/letsencrypt/live/locuszoom.occsci.com/privkey.pem
Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>
</IfModule>
```

