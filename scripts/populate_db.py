"""
Command line script to populate a testing database with a few fake studies, to enable UI testing and local development.

usage:

`python3 scripts/populate_db.py -n 10`

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

from locuszoom_plotting_service.gwas.tests.factories import AnalysisInfoFactory, AnalysisFilesetFactory  # NOQA
from locuszoom_plotting_service.users.tests.factories import UserFactory  # NOQA


def get_or_create_user(user_id: int) -> User:
    """If requested user does not exist in the DB, create it using a factory"""
    try:
        user = User.objects.get(pk=user_id)
    except Exception:
        print('User not known, searching for user id: ', user_id)
        user = UserFactory()
        print(f'Created new user <${user.display_name}>')
    return user


def create_analyses(num_analyses: int = 10,
                    user: User = None) \
        -> typing.List[AnalysisInfo]:
    # TODO: There is a major known issue: although this will populate search results, it disables ingest and
    #   therefore can't ever generate actual data pages. (so region view and manhattan plot will never render)
    analyses = [
        AnalysisInfoFactory(
            owner=user,
            files=AnalysisFilesetFactory(has_data=True, has_completed=True)
        )
        for i in range(num_analyses)
    ]
    return analyses


def parse_args():
    parser = argparse.ArgumentParser(description='Populate the database')
    parser.add_argument('-n', '--n_gwas', dest='n_gwas', type=int, default=10,
                        help='Number of GWAS analysis records to create')
    parser.add_argument('-u', '--user', dest='user_id',
                        type=str, help='User ID # of the user who will own these records')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.user_id:
        known_user = get_or_create_user(args.user_id)
    else:
        known_user = None
    analyses = create_analyses(num_analyses=args.n_gwas, user=known_user)
    print('Successfully created analyses:', analyses)
