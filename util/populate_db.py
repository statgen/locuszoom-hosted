"""
Command line script to populate a testing database with a few fake studies, to enable UI testing and local development.

usage:

`python3 util/populate_db.py -n 10`

"""
import argparse
import os
from pathlib import Path
import sys
import typing

import django

# Must configure standalone django usage before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.append(str(Path(__file__).parent.parent.resolve()))
django.setup()

from locuszoom_plotting_service.gwas.models import AnalysisInfo  # NOQA
from locuszoom_plotting_service.users.models import User  # NOQA

from locuszoom_plotting_service.gwas.tests.factories import GwasFactory  # NOQA
from locuszoom_plotting_service.users.tests.factories import UserFactory  # NOQA


def get_or_create_user(username: str) -> User:
    """If requested user does not exist in the DB, create it using a factory"""
    try:
        user = User.objects.get(username=username)
    except Exception:
        print(username)
        user = UserFactory(username=username)
        print(f'Created new user <${username}>')
    return user


def create_analyses(num_analyses: int = 10,
                    user: User = None) \
        -> typing.List[AnalysisInfo]:

    # FIXME: respect user argument
    analyses = [GwasFactory() for i in range(num_analyses)]
    return analyses


def parse_args():
    parser = argparse.ArgumentParser(description='Populate the database')
    parser.add_argument('-n', '--n_gwas', dest='n_gwas', type=int, default=10,
                        help='Number of GWAS analysis records to create')
    parser.add_argument('-u', '--user', dest='username',
                        type=str, help='Username of the user who will own these records')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.username:
        known_user = get_or_create_user(args.username)
    else:
        known_user = None
    analyses = create_analyses(num_analyses=args.n_gwas, user=known_user)
    print('Successfully created analyses:', analyses)
