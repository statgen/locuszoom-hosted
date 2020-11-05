# LocusZoom: Hosted Upload Service

Upload, analyze, and share GWAS results with LocusZoom.js. Try it at [my.locuszoom.org](https://my.locuszoom.org).


## Settings

For a basic guide to most settings, see the [cookiecutter-django docs](https://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands


### Quickstart
The following commands will start a development environment. Some IDEs (such as Pycharm) are able to run the app via run configurations, which may be more convenient than starting things through the terminal.

For production deployment instructions, see [docs/deploy/index.md](docs/deploy/index.md). 
 
- In one tab, build assets (in local development, this is currently done on the host system, outside of Docker): 

`$ yarn run prod`

or with live rebuilding, if you intend to be changing JS code as you work:

`$ yarn run dev`

- In a second open terminal::

```
$ docker system prune && docker-compose -f local.yml build --pull
$ docker-compose -f local.yml up
```

(`docker system prune` is optional, but it can save your hard drive from filling up as you experiment with different build options)

On the first installation, you will also need to download some large asset files required for annotations. For local development, a "test" version is available that will only annotate a limited subset of biologically interesting genes; this subset is much smaller than the full database, and easier to use on a laptop.

(see deployment docs for the correct command to use with production assets)

```bash
$ docker-compose -f local.yml run --rm django zorp-assets download --type snp_to_rsid_test --tag genome_build GRCh37 --no-update
$ docker-compose -f local.yml run --rm django zorp-assets download --type snp_to_rsid_test --tag genome_build GRCh38 --no-update
```

### Setting Up Your Users

- To create an **superuser account**, use the following command. This must be performed first, in order to set up
Google OAuth social authentication for everyone else::

    `$ docker-compose -f local.yml run --rm django python manage.py createsuperuser`

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox
(or similar), so that you can see how the site behaves for both kinds of users.

Then follow the [authentication setup instructions](https://django-allauth.readthedocs.io/en/latest/installation.html).

The OAuth credentials may be obtained through the Google API console. For local development, you must use named origins
  (not an IP address) for the values you enter in the console:
- Allowed origins: `http://localhost:8000`
- Authorized redirect URIs:  `http://localhost:8000/accounts/google/login/callback/`

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a
"Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link
into your browser. Now the user's email should be verified and ready to go.


- To generate database migrations within the docker container, run::

`$ docker-compose -f local.yml run --rm django python manage.py makemigrations`

Then verify the migration file is correct, and restart Docker to apply the migrations automatically. (in production, you must apply the migrations manually; see deployment guide for details)


## Development and testing helpers
### Generating sample data for testing

- A bootstrapping script has been created to populate the database with fake users and studies. To use it, run::

    `$ docker-compose -f local.yml run --rm django python3 scripts/populate_db.py -n 10`

This script generates fake studies for search results, but it notably does not run the ingest pipeline.
 It may be improved in the future to generate more realistic and complete fake data. 

### Opening a terminal for debugging
Because all development happens inside a Docker container, it is sometimes useful to open a terminal for debugging
purposes. This can be done as follows.

On a running container::

`$ docker-compose -f local.yml exec django bash`

Create a container just to run a command::

`$ docker-compose -f local.yml run --rm django bash`

Similarly, the django app can be probed interactively (eg, to experiment with the ORM) via an enhanced python shell::

`$ docker-compose -f local.yml run --rm django ./manage.py shell_plus`


### Static analysis checks

We run static analysis with flake8, and type checks with mypy:::

`$ flake8 .`
`$ mypy .`

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report::

`$ coverage run -m pytest`
`$ coverage html`
`$ open htmlcov/index.html`

### Running tests with py.test
A suite of unit tests is available::

`$ docker-compose -f local.yml run --rm django pytest`

## Sentry

Sentry is an error logging aggregator service. If a key (DSN) is provided in your .env file, errors will be tracked
 automatically.

## Deployment

### Docker
This app uses Docker to manage dependencies and create a working environment. See 
[deployment documentation](docs/deploy/index.md) for instructions on how to create a working, production server 
environment. A local, debug-friendly Docker configuration is also provided in this repo, and many of the instructions 
in this document assume this is what you will use. 
 
 The original Docker configuration has been modified from cookiecutter-django; see their docs for more information 
 about default options and design choices.  
