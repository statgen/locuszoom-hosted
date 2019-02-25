import os
import random

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import signals
import factory

from locuszoom_plotting_service.users.tests.factories import UserFactory
from .. import constants as lz_constants
from ..models import Gwas


def choose_genome_build() -> str:
    return random.choice(lz_constants.GENOME_BUILDS)[0]


def choose_imputation_panel() -> str:
    return random.choice(lz_constants.IMPUTATION_PANELS)[0]

# TODO: find a way to keep test runs from cluttering FS with 0B files; temp folder maybe?


@factory.django.mute_signals(signals.post_save)
class GwasFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(UserFactory)
    analysis = factory.Faker('words', nb=2)

    build = factory.LazyFunction(choose_genome_build)
    imputed = factory.LazyFunction(choose_imputation_panel)
    is_log_pvalue = False

    is_public = False

    ingest_complete = None

    raw_gwas_file = factory.django.FileField(from_func=lambda: SimpleUploadedFile('fictional.txt', content=''))

    class Meta:
        model = Gwas

    class Params:
        # Most samples will be fine with a 0B file. Only provide actual data if explicitly requested.
        has_data = factory.Trait(
            raw_gwas_file=factory.django.FileField(
                from_path=os.path.join(os.path.dirname(__file__), 'fixtures/placeholder.txt'))
        )
