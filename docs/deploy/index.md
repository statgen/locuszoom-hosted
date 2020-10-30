# Deployment instructions
Deployment has been tested on Ubuntu 16.04 LTS. Other systems may work, but have not been tested.

## System requirements
The hosted LocusZoom app is run inside a Docker container, but the web server (eg apache) is left to the host machine. This configuration was chosen because our production app runs on shared hardware, but there is no technical reason why the server could not be containerized as well in principle. Sample configuration files are provided where appropriate.

- Apache 2
    - Several modules must be enabled (`sudo a2enmod ssl proxy_http headers rewrite`)
    - All examples assume that you have enabled HTTPS in production. We use [Certbot + LetsEncrypt](https://certbot.eff.org/lets-encrypt/). 
- [Docker](https://docs.docker.com/engine/install/ubuntu/) 
- [Docker Compose](https://docs.docker.com/compose/install/)


## Required server configuration
### Apache virtualhosts
The app is run within a Docker container, and reached from the outside world via a reverse proxy. Sample config is 
provided for Apache2. 

Install the provided `sample-apache.conf` file (editing the `ServerName` as appropriate), and reload Apache. 
Be sure to provide an SSL certificate for your hostname (eg LetsEncrypt). 

### Storage locations
On the host system, create a folder `/var/lz-uploads`. This will be mounted to Docker where all user-uploaded GWAS
files will be stored.

`sudo groupadd lzupload`
`sudo chgrp lzupload lz-uploads/`
`sudo chmod g+s lz-uploads/`

## Required app configuration
Create two config files describing the production environment and populate secrets, config variables, etc according to 
the pre-populated templates: `.envs/.production/.django` and `.envs/.production/.postgres`

(sample files are provided; copy them from `*-sample` to match the names above) 

Be sure to keep your production settings private!

## Build and deployment
Build the Docker container in production (in the future we may create a pre-built image):
`sudo docker-compose -f production.yml build --pull`

Start the container:
`sudo docker-compose -f production.yml up -d`

This app uses internal django features to serve static assets, so those do not require a separate deploy step.

## Once the app is running...
### Run migrations for the first time to set up the database
`$ sudo docker-compose -f production.yml run --rm django python manage.py migrate`

### Load sample data required for base functionality

The "find rsID for SNP" feature requires downloading premade lookup tables from our server.

```bash
$ docker-compose -f production.yml run --rm django zorp-assets download --type snp_to_rsid --tag genome_build GRCh37 --no-update
$ docker-compose -f production.yml run --rm django zorp-assets download --type snp_to_rsid --tag genome_build GRCh38 --no-update
```

### Create an admin user
You will need to enter some configuration into the admin panel before using the app for the first time.

In production, your admin site must be hidden behind an obfuscated URL. This is determined by the `DJANGO_ADMIN_URL`
 setting in `.envs/.production/.django`.

Use the following command to create an admin user. Be sure to protect these credentials!
`$ sudo docker-compose -f production.yml run --rm django python manage.py createsuperuser`

### OAuth settings
This site uses social OAuth login via Django-allauth. In order to log in, you will need to follow the [auth setup instructions](https://django-allauth.readthedocs.io/en/latest/installation.html) to register OAuth credentials (client ID and secret) for your local app. The site URL must match the callback registered with the OAuth provider.

You do not need to create a `Site` entry in the Django admin, as the app will do this automatically for you on first startup (based on the `LZ_OFFICIAL_URL` registered in your .env file)

A sample callback URL for OAuth registration (in local development) would be:
    http://localhost:8000/accounts/google/login/callback/

(Replace the hostname and port with your own production URL).


## Releasing a new version (checklist)
- `docker-compose -f production.yml build --pull`
- `docker-compose -f production.yml up -d`
- (optional) `docker-compose -f production.yml run --rm django python manage.py migrate`

### Monitoring the new release
- Monitor new error reports from Sentry
- Watch application logs during manual QA via: `docker-compose -f production.yml logs --follow --tail 20`
