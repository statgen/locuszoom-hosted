import logging
import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.http import urlencode
from django.urls import reverse
from model_utils.models import TimeStampedModel

from . import constants
from . import util

logger = logging.getLogger(__name__)

User = get_user_model()

# class Phenotypes(models.Model):
#     """Pre-defined lists of phenotypes: ICD9, ICD10, EFO, or Vanderbilt phecodes"""
#     short_desc = models.CharField()
#     long_desc = models.CharField()
#     classification = None  # TODO: Create enum or other system


def _pipeline_folder():
    # Get pipeline folder name; must be a standalone function for migrations to work
    return uuid.uuid1().hex


class AnalysisInfo(TimeStampedModel):
    """
    Metadata describing a single analysis (GWAS results). Typically associated with an `AnalysisFile`
    """
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    label = models.CharField(max_length=100,
                             help_text='A human-readable description, eg DIAGRAM Height GWAS')

    is_public = models.BooleanField(default=False, help_text='Is this study visible to everyone?')

    # User-provided study metadata
    pmid = models.CharField(max_length=20,
                            blank=True,
                            null=True,
                            help_text='The PubMed ID associated with a published GWAS',
                            verbose_name='PMID')

    build = models.CharField(max_length=10, choices=constants.GENOME_BUILDS)
    imputed = models.CharField(max_length=25, blank=True,
                               # TODO Too restrictive; provide an "other" option?
                               choices=constants.IMPUTATION_PANELS,
                               help_text='If your data was imputed, please specify the reference panel used')

    n_cases = models.PositiveIntegerField(blank=True, null=True, help_text='Number of phenotype cases in sample')
    n_controls = models.PositiveIntegerField(blank=True, null=True, help_text='Number of phenotype controls in sample')

    parser_options = JSONField(null=False, blank=False, default={},  # Uploads must tell us how to parse
                               help_text='Parser options (zorp-compatible parser kwarg names)')

    # Data to be filled in by upload/ post processing steps
    top_hit_view = models.OneToOneField('gwas.RegionView', on_delete=models.SET_NULL, null=True)

    ingest_status = models.IntegerField(choices=constants.INGEST_STATES, default=0,
                                        help_text='Track progress of data ingestion')  # All-or-nothing!
    ingest_complete = models.DateTimeField(null=True,
                                           help_text='When the ingestion pipeline completed (success or failure)')

    ########
    # Below this line: Track info needed to serve data from local files
    pipeline_path = models.CharField(max_length=32,
                                     default=_pipeline_folder,
                                     help_text='Internal use only: path to folder of ingested data')
    raw_gwas_file = models.FileField(upload_to=util.get_gwas_raw_fn,
                                     verbose_name='GWAS file',
                                     help_text='The GWAS data to be uploaded. May be text-based, or (b)gzip compressed')
    file_sha256 = models.BinaryField(max_length=32,
                                     help_text='The hash of the original, raw uploaded file')

    def get_absolute_url(self):
        return reverse('gwas:overview', kwargs={'pk': self.id})

    def __str__(self):
        return self.label

    def can_view(self, current_user):
        """
        # FIXME: This is a simplest-possible permissions model; revise as app grows in complexity.
        :param request:
        :return:
        """
        return self.is_public or (current_user == self.owner)

    #######
    # Helpers defining where to find/ store each asset
    @property
    def normalized_gwas_path(self):
        """Path to the normalized, tabix-indexed GWAS file"""
        return os.path.join(util.get_study_folder(self, absolute_path=True), 'normalized.txt.gz')

    @property
    def normalized_gwas_log_path(self):
        """Path to the normalized, tabix-indexed GWAS file"""
        return os.path.join(util.get_study_folder(self, absolute_path=True), 'normalized.log')

    @property
    def manhattan_path(self):
        # PheWeb pipeline writes a JSON file that is used in entirety by frontend
        return os.path.join(util.get_study_folder(self, absolute_path=True), 'manhattan.json')

    @property
    def qq_path(self):
        return os.path.join(util.get_study_folder(self, absolute_path=True), 'qq.json')

    @property
    def tophits_path(self):
        # PheWeb pipeline writes a tabixed file that supports region queries # TODO: Implement
        return os.path.join(util.get_study_folder(self, absolute_path=True), 'tophits.gz')


class OntologyTerm(models.Model):
    """Available classification schemes that can be used to tag studies- eg SNOMED CT, PheCode, or ICD10"""
    code = models.CharField(unique=True,
                            max_length=20,
                            db_index=True,
                            help_text="The unique identifier used by the nomenclature system")
    label = models.TextField(help_text="A human-readable description of the code")
    scheme = models.SmallIntegerField(
        choices=(
            (1, 'SNOMED CT'),
        ),
        help_text="The classification scheme (SNOMED, ICDx, etc)"
    )

    class Meta:
        unique_together = ('code', 'scheme')


class RegionView(TimeStampedModel):
    """
    Represents an interesting locus region, with optional config parameters

    The upload pipeline will define a few suggested views (eg top hits), and users can save their own views on any
        public dataset
    """
    # What is this view associated with? Allows users to save views for someone else's (public) datasets
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)  # Null for views created by system

    label = models.CharField(max_length=100)

    # What region to view?
    chrom = models.CharField(max_length=5, blank=False)  # Standardize with PheWeb chroms list?
    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()

    options = JSONField(null=True, blank=True,  # TODO: decouple front and back end as requirements evolve
                        help_text="Additional arbitrary params associated with the page- URL query params. (eg plot features or options)")

    def can_view(self, current_user):
        """View permissions are solely determined by the underlying study"""
        # TODO: Fix backrefs here; sort out relationships.
        return self.gwas.can_view(current_user)

    def get_absolute_url(self):
        """A region view is just a LocusZoom plot with some specific options"""
        base_url = reverse('gwas:region', kwargs={'pk': self.gwas.id})
        params = urlencode(self.get_url_params())
        return f'{base_url}?{params}'

    # Helper methods
    def get_url_params(self):
        # The standalone fields are source of truth and override any values stored in the "extra" params blob
        basic = {'chrom': self.chrom, 'start': self.start, 'end': self.end}
        extended = self.options or {}
        return {**extended, **basic}

