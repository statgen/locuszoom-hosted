locuszoom_plotting_service
==========================

Upload and share GWAS results with LocusZoom.js

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django


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

    $ npm run dev

or with live rebuilding, if you intend to be changing JS code as you work::

    $ npm run prod


* In a second open terminal::

    $ docker-compose -f local.yml build
    $ docker-compose -f local.yml up


Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a
"Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link
into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox
(or similar), so that you can see how the site behaves for both kinds of users.


* To generate database migrations within the docker container, run::

    $ docker-compose -f local.yml run --rm django python manage.py makemigrations


Then verify the migration file is correct, and restart docker to apply the migrations automatically.


Generating sample data for testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* A bootstrapping script has been created to populate the database with fake users and studies. To use it, run::

    $ docker-compose -f local.yml run --rm django python3 util/populate_db.py -n 10


Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy locuszoom_plotting_service

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ docker-compose -f local.yml run --rm django pytest

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: https://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html



Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd locuszoom_plotting_service
    celery -A locuszoom_plotting_service.taskapp worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the
same folder with *manage.py*, you should be right.




Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at
https://sentry.io/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.


Deployment
----------

The following details how to deploy this application.



Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: https://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html



