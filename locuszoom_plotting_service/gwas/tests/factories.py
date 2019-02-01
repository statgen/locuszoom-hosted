import os
import random

import factory

from locuszoom_plotting_service.users.tests.factories import UserFactory
from .. import constants as lz_constants
from ..models import Gwas

def choose_genome_build() -> str:
    return random.choice(lz_constants.GENOME_BUILDS)[0]


def choose_imputation_panel() -> str:
    return random.choice(lz_constants.IMPUTATION_PANELS)[0]


class GwasFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    analysis = factory.Faker('word')

    build = factory.LazyFunction(choose_genome_build)
    imputed = factory.LazyFunction(choose_imputation_panel)
    is_log_pvalue = False

    raw_gwas_file = factory.django.FileField(from_path=os.path.join(os.path.dirname(__file__), 'fixtures/placeholder.txt'))

    class Meta:
        model = Gwas
