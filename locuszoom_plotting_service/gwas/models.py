import logging
import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.http import urlencode
from django.urls import reverse
from model_utils.models import TimeStampedModel

from ..base.util import _generate_slug
from . import constants
from . import util


logger = logging.getLogger(__name__)

User = get_user_model()


def _pipeline_folder():
    """Get pipeline folder name; must be a standalone function for migrations to work"""
    return uuid.uuid1().hex


class AnalysisInfo(TimeStampedModel):
    """
    Metadata describing a single analysis (GWAS results). Typically associated with an `AnalysisFileset`
    """
    slug = models.SlugField(max_length=6, unique=True, editable=False, default=_generate_slug,
                            help_text="The external facing identifier for this record")

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # One user, many gwas
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

    n_cases = models.PositiveIntegerField(blank=True, null=True, help_text='Number of phenotype cases in sample')
    n_controls = models.PositiveIntegerField(blank=True, null=True, help_text='Number of phenotype controls in sample')

    # Data to be filled in by upload/ post processing steps
    files = models.OneToOneField(  # Only one set of files is "current" at any time
        'gwas.AnalysisFileset',
        on_delete=models.SET_NULL,
        null=True,
        help_text='Where to find the processed, ingested data file for this analysis (most recently finished version)'
    )
    top_hit_view = models.OneToOneField('gwas.RegionView',
                                        related_name='+',
                                        on_delete=models.SET_NULL,
                                        null=True)

    def get_absolute_url(self):
        return reverse('gwas:overview', kwargs={'slug': self.slug})

    def can_view(self, current_user):
        """
        # FIXME: This is a simplest-possible permissions model; revise as app grows in complexity.
        :param User current_user: An object representing the current user (logged in or anon)
        :return:
        """
        # In simplest form, this allows viewing of public, "ingest pending/failed" studies by other people
        return self.is_public or (current_user == self.owner)

    # Useful calculated properties
    @property
    def most_recent_upload(self):
        return self.analysisfileset_set.order_by('-created').first()

    @property
    def ingest_status(self) -> int:
        """
        Get ingest status: if view does not point to a specific version, then default to whatever was uploaded recently
        """

        if self.files:
            return self.files.ingest_status

        most_recent_upload = self.most_recent_upload
        if not most_recent_upload:  # Somehow we have metadata without any corresponding file!! Mark as an error.
            return 1

        return most_recent_upload.ingest_status

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        """Generate a slug and ensure it is unique"""
        while True:  # Ensure creation of a random, unique slug
            if self.pk:  # ...but only if the record is new
                break

            slug = _generate_slug()
            if not AnalysisInfo.objects.filter(slug=slug).first():
                self.slug = slug
                break

        super().save(*args, **kwargs)


class AnalysisFileset(TimeStampedModel):
    """
    This represents the data associated with a particular `AnalysisInfo` model. We use a separate model so that a study
    can be updated or reprocessed cleanly if needed (it simplifies things like versioning).

    It contains a direct reference to one file (the uploaded one), but also refers to local paths for several others
    output by the ingest step
    """
    metadata = models.ForeignKey(AnalysisInfo, on_delete=models.SET_NULL, null=True)

    # Basic file data
    pipeline_path = models.CharField(max_length=32,
                                     default=_pipeline_folder,
                                     help_text='Internal use only: path to folder of ingested data. Value auto-set.')
    raw_gwas_file = models.FileField(upload_to=util.get_gwas_raw_fn,
                                     verbose_name='GWAS file',
                                     help_text='The GWAS data to be uploaded. May be text-based, or (b)gzip compressed')
    file_sha256 = models.BinaryField(max_length=32,
                                     help_text='The hash of the original, raw uploaded file')

    # Options related to the ingestion pipeline
    parser_options = JSONField(null=False,
                               blank=False,
                               default={},  # Uploads must tell us how to they are parsed
                               help_text='Parser options (zorp-compatible parser kwarg names)')

    ingest_status = models.IntegerField(choices=constants.INGEST_STATES, default=0,
                                        help_text='Track progress of data ingestion')  # All-or-nothing!
    ingest_complete = models.DateTimeField(null=True,
                                           help_text='When the file finished processing (success OR failure)')

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
        choices=constants.PHENO_CLASSIFICATIONS,
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
    gwas = models.ForeignKey(AnalysisInfo,
                             on_delete=models.SET_NULL,
                             null=True,
                             help_text='The study associated with this view')

    label = models.CharField(max_length=100, help_text='A human-readable description of this view')

    # What region to view?
    chrom = models.CharField(max_length=5, blank=False)  # Standardize with PheWeb chroms list?
    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()

    # options = JSONField(null=True, blank=True,  # TODO: not used now, may be useful in the future
    #                     help_text="Additional URL query params to be sent to the front end. (eg for plot features)")

    def can_view(self, current_user):
        """View permissions are solely determined by the underlying study"""
        # TODO: Fix backrefs here; sort out relationships.
        return self.gwas.can_view(current_user)

    def get_absolute_url(self):
        """A region view is just a LocusZoom plot with some specific options"""
        # This references the backref for top hit view but this should be extended to allow many-to-many rels.
        base_url = reverse('gwas:region', kwargs={'slug': self.gwas.slug})
        params = urlencode(self.get_url_params())
        return f'{base_url}?{params}'

    # Helper methods
    def get_url_params(self):
        # The standalone fields are source of truth and override any values stored in the "extra" params blob
        basic = {'chrom': self.chrom, 'start': self.start, 'end': self.end}
        # extended = self.options or {}
        # return {**extended, **basic}
        return basic
