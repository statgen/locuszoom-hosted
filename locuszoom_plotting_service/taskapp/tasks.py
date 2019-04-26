import os

from celery.utils.log import get_task_logger
from celery import shared_task
from django.conf import settings
from django.core.mail import mail_admins, send_mail
from django.db.models import signals
from django.dispatch import receiver
from django.utils import timezone

from locuszoom_plotting_service.gwas import models
from util.ingest import (
    exceptions,
    processors,
    validators
)


logger = get_task_logger(__name__)


@shared_task(bind=True)
def hash_contents(self, gwas_id: int):
    """Store a unique hash of the file contents"""
    instance = models.Gwas.objects.get(pk=gwas_id)
    sha256 = processors.get_file_sha256(os.path.join(settings.MEDIA_ROOT, instance.raw_gwas_file.name))
    instance.file_sha256 = sha256
    instance.save()


@shared_task(bind=True)
def normalize_gwas(self, gwas_id: int):
    instance = models.Gwas.objects.get(pk=gwas_id)

    src_path = os.path.join(settings.MEDIA_ROOT, instance.raw_gwas_file.name)
    dest_path = instance.normalized_gwas_path
    parser_options = instance.parser_options

    log_path = instance.normalized_gwas_log_path

    if not validators.standard_gwas_validator.validate(src_path, instance.parser_options):
        logger.info(f"Could not load GWAS '{src_path}' because contents failed to validate")
        raise exceptions.ValidationException(f'Validation failed for study ID {gwas_id}')

    # For now the writer expects a temp file name, and it creates the .gz version internally
    tmp_normalized_path = dest_path.replace('.txt.gz', '.txt')
    processors.normalize_contents(src_path, parser_options, tmp_normalized_path, log_path)


@shared_task(bind=True)
def summarize_gwas(self, gwas_id: int):
    """Generate "summary" files based on the overall study contents; uses PheWeb loader code"""
    instance = models.Gwas.objects.get(pk=gwas_id)
    normalized_path = instance.normalized_gwas_path
    manhattan_path = instance.manhattan_path
    qq_path = instance.qq_path

    # Find top hit
    best_row = processors.get_top_hit(normalized_path)
    top_hit = models.RegionView.objects.create(
        label='Top hit',
        chrom=best_row.chrom,
        start=best_row.pos - 250_000,
        end=best_row.pos + 250_000
    )
    instance.top_hit_view = top_hit
    instance.save()

    # Generate files
    processors.generate_manhattan(normalized_path, manhattan_path)
    processors.generate_qq(normalized_path, qq_path)


@shared_task(bind=True)
def mark_success(self, gwas_id):
    """Notify the owner of a gwas that ingestion has successfully completed"""
    instance = models.Gwas.objects.get(pk=gwas_id)

    instance.ingest_status = 2
    instance.ingest_complete = timezone.now()
    instance.save()

    send_mail('Results done processing',
              f'Your results are done processing. Please visit {instance.get_absolute_url()} to see the Manhattan plot.',
              'noreply@umich.edu',
              [instance.owner.email])


@shared_task(bind=True)
def mark_failure(self, gwas_id):
    """Mark a task as failed, and email site admins. Eventually, we can dial back the error emails a bit."""
    instance = models.Gwas.objects.get(pk=gwas_id)

    logger.exception(f'Ingestion pipeline failed for gwas id: {gwas_id}')
    instance.ingest_status = 1
    instance.ingest_complete = timezone.now()
    instance.save()

    mail_admins('Results done processing',
                f'Data ingestion failed for gwas id: {gwas_id}. Please see logs for details.'
    )


def total_pipeline(gwas_id: int):
    """Combine discrete tasks into a total pipeline"""
    instance = models.Gwas.objects.get(pk=gwas_id)

    return (
        hash_contents.si(gwas_id) |
        normalize_gwas.si(gwas_id) |
        summarize_gwas.si(gwas_id) |
        mark_success.si(gwas_id)
    ).on_error(mark_failure.si(gwas_id))


@receiver(signals.post_save, sender=models.Gwas)
def gwas_upload_signal(sender, instance: models.Gwas = None, created=None, **kwargs):
    """
    Run the ingest pipeline whenever a new record is created in the database

    Thin wrapper to start a celery task.
    """
    # Only run once when model first created.
    # This is a safeguard to prevent infinite recursion from re-saves
    if not created or not instance:
        return

    total_pipeline(instance.pk).apply_async()
