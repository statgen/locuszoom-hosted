import os
import random

from django.db.models import signals
from django.utils import timezone
import factory

from locuszoom_plotting_service.users.tests.factories import UserFactory
from .. import constants as lz_constants
from .. import models as lz_models


def choose_genome_build() -> str:
    return random.choice(lz_constants.GENOME_BUILDS)[0]


def choose_consortium() -> str:
    return random.choice(['LocusZoom JS', 'LocusZoom Standalone', 'LocusZoom Hosted', 'LocusZoom.org'])


@factory.django.mute_signals(signals.post_save)
class AnalysisFilesetFactory(factory.DjangoModelFactory):
    raw_gwas_file = None  # Only create temp files if has_data trait is True

    ingest_status = 0  # pending (most tests don't run celery tasks, and therefore are "pending" processing)
    ingest_complete = None

    parser_options = factory.Dict({  # Parser options for standard gwas format
        'chrom_col': 1,
        'pos_col': 2,
        'ref_col': 3,
        'alt_col': 4,
        'pvalue_col': 5,
        'is_neg_log_pvalue': False
    })

    class Meta:
        model = lz_models.AnalysisFileset

    class Params:
        # Most samples will be fine with a 0B file. Only provide actual data if explicitly requested.
        has_data = factory.Trait(
            raw_gwas_file=factory.django.FileField(
                from_path=os.path.join(os.path.dirname(__file__), 'fixtures/placeholder.txt'))
        )

        has_completed = factory.Trait(  # Marks pipeline complete (without actually running it)
            ingest_complete=timezone.now(),
            ingest_status=2
        )


class AnalysisInfoFactory(factory.DjangoModelFactory):
    owner = factory.SubFactory(UserFactory)
    label = factory.Faker('sentence', nb_words=2)
    study_name = factory.LazyFunction(choose_consortium)

    files = factory.SubFactory(AnalysisFilesetFactory)

    build = factory.LazyFunction(choose_genome_build)

    is_public = False

    class Meta:
        model = lz_models.AnalysisInfo


class ViewLinkFactory(factory.DjangoModelFactory):
    label = factory.Faker('sentence', nb_words=2)
    gwas = factory.SubFactory(AnalysisInfoFactory)

    class Meta:
        model = lz_models.ViewLink
