locuszoom_plotting_service
==========================

Upload and share GWAS results with LocusZoom.js

:License: MIT


Settings
--------

Moved to settings_.

.. _settings: https://cookiecutter-django.readthedocs.io/en/latest/settings.html

Basic Commands
--------------

Quickstart
^^^^^^^^^^^

The following commands will start a development environment.


* In one tab, build assets::

    $ yarn run prod

or with live rebuilding, if you intend to be changing JS code as you work::

    $ yarn run dev


* In a second open terminal::

    $ docker-compose -f local.yml build
    $ docker-compose -f local.yml up


Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create an **superuser account**, use the following command. This must be performed first, in order to set up
Google OAuth social authentication for everyone else::

    $ docker-compose -f local.yml run --rm django python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox
(or similar), so that you can see how the site behaves for both kinds of users.

Then follow the _`social-auth` setup instructions. If you encounter a django error when adding a new Site under
admin, retry. (this is a known issue)
.. _:https://django-allauth.readthedocs.io/en/latest/installation.html


The OAuth credentials may be obtained through the Google API console. For local development, you must use named origins
  (not an IP address) for the values you enter in the console:
Allowed origins: `http://localhost:8000`
Authorized redirect URIs:  `http://localhost:8000/accounts/google/login/callback/`

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a
"Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link
into your browser. Now the user's email should be verified and ready to go.


* To generate database migrations within the docker container, run::

    $ docker-compose -f local.yml run --rm django python manage.py makemigrations


Then verify the migration file is correct, and restart docker to apply the migrations automatically.




Generating sample data for testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* A bootstrapping script has been created to populate the database with fake users and studies. To use it, run::

    $ docker-compose -f local.yml run --rm django python3 scripts/populate_db.py -n 10



Opening a terminal for debugging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Because all development happens inside a docker container, it is sometimes useful to open a terminal for debugging
purposes. This can be done as follows.

On a running container::

    $ docker-compose -f local.yml exec django bash

Create a container just to run a command::

    $ docker-compose -f local.yml run --rm django bash


Similarly, the django app can be probed interactively (eg, to experiment with the ORM) via an enhanced python shell::

    $ docker-compose -f local.yml run --rm django ./manage.py shell_plus


Static analysis checks
^^^^^^^^^^^^^^^^^^^^^^^

We run static analysis with flake8, and type checks with mypy:::

  $ flake8 .
  $ mypy .



Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

A suite of unit tests is available::

  $ docker-compose -f local.yml run --rm django pytest

Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd locuszoom_plotting_service
    celery -A locuszoom_plotting_service.taskapp worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the
same folder with *manage.py*, you should be ok.


Sentry
^^^^^^

Sentry is an error logging aggregator service. If a key (DSN) is provided in your .env file, errors will be tracked
 automatically. You will need one DSN each for your frontend (JS) and backend (python) code.

Deployment
----------

The following details how to deploy this application.


Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: https://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html

And `specific instructions for this app`:
.. _`specific instructions for this app`: deploy/index.md

(future) Initializing the app with default data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Certain app features, such as "tagging datasets", will require loading initial data into the database.

This feature is not yet used in production, but the notes below demonstrate loader scripts in progress.

These datasets may be large or restricted by licensing rules; as such, they are not distributed with the code and must
be downloaded/reprocessed separately for loading.

- _`SNOMED CT (Core) / May 2019`
.. _:https://www.nlm.nih.gov/research/umls/Snomed/core_subset.html


These files must be downloaded separately due to license issues (they cannot be distributed with this repo).
Run the appropriate scripts in `scripts/data_loaders/` to transform them into a format suitable for django usage.

After creating the app, run the following command (once) to load them in (using the appropriate docker-compose file)::

    $ docker-compose -f local.yml run --rm django python3 manage.py loaddata scripts/data_loaders/sources/snomed.json

(TODO: additional/modified commands may be required to do this in production)


.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
