import gzip
import hashlib
import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils import timezone
from django.utils.http import urlencode
from django.urls import reverse
from model_utils.models import TimeStampedModel

from pheweb.load import manhattan
import pysam

from . import constants


User = get_user_model()


class Gwas(TimeStampedModel):
    """A single analysis (GWAS results) that may be part of a larger group"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    analysis = models.CharField(max_length=100, help_text="A human-label describing the analysis performed, eg DIAGRAM Height GWAS")

    # Metadata that the user must fill in when uploading
    build = models.CharField(max_length=10, choices=constants.GENOME_BUILDS)  # TODO: Make this a db table
    imputed = models.CharField(max_length=25, blank=True)  # TODO: prefill options to the imputation server default choices
    is_log_pvalue = models.BooleanField(default=True)

    # Data to be filled in by upload/ post processing steps
    top_hit_view = models.OneToOneField('gwas.RegionView', on_delete=models.SET_NULL, null=True, related_name='+')
    pipeline_complete = models.DateTimeField(null=True)

    ########
    # Below this line: first iteration will be to serve files from local filesystem, rather than database
    file_location = models.FileField()
    file_sha256 = models.CharField(max_length=64)

    ## TODO: Future: tell the server how to parse this GWAS file. For first iteration, assume a file format that we control.
    # marker_col_name = models.CharField(default='MarkerName', max_length=25)
    # pvalue_col = models.CharField(default='P.value', max_length=25)
    # delimiter = models.CharField(
    #     max_length=25,
    #     choices=(
    #         (r'\t', 'Tab'),
    #         (',', 'Comma'),
    #         (' ', 'Space'),
    #         (r'\s', 'Whitespace')
    #     )
    # )

    @property
    def file_size(self):
        return self.file_location.size

    @property
    def manhattan_fn(self):
        return os.path.splitext(self.file_location.name)[0] + '.json'

    def get_absolute_url(self):
        return reverse('gwas-summary', kwargs={'pk': self.id})

    def __str__(self):
        return self.analysis


class RegionView(TimeStampedModel):
    """
    Represents an interesting locus region, with optional config parameters

    The upload pipeline will define a few suggested views (eg top hits), and users can save their own views on any
        public dataset
    """
    # What is this view associated with? Allows users to save views for someone else's (public) datasets
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)  # Null for admin/ upload pipeline created views?
    gwas = models.ForeignKey(Gwas, on_delete=models.DO_NOTHING)

    label = models.CharField(max_length=100)

    # What region to view?
    chrom = models.CharField(max_length=5, blank=False)  # 1, X, Y, MT, etc. TODO: Standardize names with Pheweb allowed choices
    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()

    # Additional arbitrary params associated with the page- URL query params
    options = JSONField(null=True, blank=True)  # TODO: Decouple front and backend as requirements emerge

    def get_absolute_url(self):
        """A region view is just a LocusZoom plot with some specific options"""
        base_url = reverse('gwas-locus', kwargs={'pk': self.gwas.id})
        params = urlencode(self.get_url_params())
        return f'{base_url}?{params}'

    # Helper methods
    def get_url_params(self):
        # The standalone fields are source of truth and override any values stored in the "extra" params blob
        basic = {'chrom': self.chrom, 'start': self.start, 'end': self.end}
        extended = self.options or {}
        return {**extended, **basic}


@receiver(signals.post_save, sender=Gwas)
def analysis_upload_pipeline(sender, instance=None, created=None, **kwargs):
    """
    Specify a series of operations to be run on a newly uploaded file, such as integrity verification and
        "interesting region" detection

    - Compute SHA
    - Find top hit(s)
    - Write data for a pheweb-style manhattan plot
    :return:
    """
    # Only run once when model first created.
    # This is a safeguard to prevent infinite recursion from re-saves (a downside of using signals)
    if not created:
        return

    # We track the SHA of what was uploaded as proof of version, but we transform what was actually stored
    with instance.file_location.open('rb') as f:
        shasum_256 = hashlib.sha256()
        if f.multiple_chunks():
           for chunk in f.chunks():
               shasum_256.update(chunk)
        else:
            shasum_256.update(f.read())

    instance.file_sha256 = shasum_256.hexdigest()

    old_fn = os.path.join(settings.MEDIA_ROOT, instance.file_location.name)
    new_fn = pysam.tabix_index(old_fn, seq_col=0, start_col=1, end_col=1, line_skip=1) # TODO: These columns are probably not the ideal everywhere
    instance.file_location.name = new_fn

    best_chrom = None
    best_pos = None
    best_pvalue = 1
    # TODO: Pheweb pipeline only supports a limited set of chromosomes:
    #   https://github.com/statgen/pheweb#3-prepare-your-association-files
    binner = manhattan.Binner()

    # TODO: Replace this with some sort of top hits per dataset feature
    with gzip.open(instance.file_location.name, 'rb') as all_rows:
        next(all_rows) # FIXME: skip header rows
        for r in all_rows:
            chrom, pos, _, _, pval = r.strip().decode().split('\t')  # TODO: Configurable parser later
            pval = float(pval)
            pos = int(pos)
            binner.process_variant({'chrom': chrom, 'pos': pos, 'pval': pval})
            if pval < best_pvalue:
                best_chrom = chrom
                best_pos = pos
                best_pvalue = pval

    top_hit_view = RegionView(gwas=instance, label="Top Hit", chrom=best_chrom, start=max(best_pos - 100_000, 0), end=(best_pos + 100000))
    top_hit_view.save()
    instance.top_hit_view = top_hit_view

    manhattan_data = binner.get_result()
    with open(instance.manhattan_fn, 'w') as f:
        json.dump(manhattan_data, f)

    # instance.top_hit_view = top_hit_view
    # TODO: Make these options configurable. These ones are for specific test data from pheweb
    # TODO: How will we handle cleanup of tabix files when db records are deleted? (eg post_delete listener; consider soft deletes)
    # Mark analysis pipeline as having completed successfully
    instance.pipeline_complete = timezone.now()

    instance.save()
