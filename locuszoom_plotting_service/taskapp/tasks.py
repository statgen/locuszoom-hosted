import functools
import os

from celery.utils.log import get_task_logger
from celery import shared_task
from django.conf import settings
from django.core.mail import mail_admins, send_mail
from django.db.models import signals
from django.db import transaction
from django.dispatch import receiver
from django.utils import timezone

from locuszoom_plotting_service.gwas import models
from util.ingest import (
    exceptions,
    processors,
    validators
)


logger = get_task_logger(__name__)


def lz_file_prep(step_name):
    """Prepare a task that operates on files, and logs success/ failure.
    The tasks we define here ACTUALLY receive IDs, which are magically converted into a DB instance before being run
    """
    def decorator(func):
        @functools.wraps(func)
        def inner(self, fileset_id: int):
            instance = models.AnalysisFileset.objects.get(pk=fileset_id)
            log_path = instance.normalized_gwas_log_path
            message = '[ingest][{}] Performing upload step: {}\n'.format(
                timezone.now().replace(microsecond=0).isoformat(),
                step_name
            )
            try:
                func(self, instance)
                message += '[success][{}] Step completed\n'.format(timezone.now().replace(microsecond=0).isoformat())
            except Exception as e:
                message += '[failure][{}] An error prevented this step from completing\n'.format(
                    timezone.now().replace(microsecond=0).isoformat())
                message += str(e) + '\n'
                raise e
            finally:
                with open(log_path, 'a+') as f:
                    f.write(message)
        return inner
    return decorator


@shared_task(bind=True)
@lz_file_prep("Calculate SHA256")
def hash_contents(self, instance: models.AnalysisFileset):
    """Store a unique hash of the file contents"""
    # instance = models.AnalysisFileset.objects.get(pk=fileset_id)

    sha256 = processors.get_file_sha256(os.path.join(settings.MEDIA_ROOT, instance.raw_gwas_file.name))
    instance.file_sha256 = sha256
    instance.save()


@shared_task(bind=True)
@lz_file_prep("Normalize GWAS file format")
def normalize_gwas(self, instance: models.AnalysisFileset):
    src_path = os.path.join(settings.MEDIA_ROOT, instance.raw_gwas_file.name)
    dest_path = instance.normalized_gwas_path
    parser_options = instance.parser_options

    log_path = instance.normalized_gwas_log_path

    if not validators.standard_gwas_validator.validate(src_path, instance.parser_options):
        logger.info(f"Could not load GWAS '{src_path}' because contents failed to validate")
        raise exceptions.ValidationException(f'Validation failed for study ID {instance.metadata.slug}')

    # For now the writer expects a temp file name, and it creates the .gz version internally
    tmp_normalized_path = dest_path.replace('.txt.gz', '.txt')
    processors.normalize_contents(src_path, parser_options, tmp_normalized_path, log_path)


@shared_task(bind=True)
@lz_file_prep("QQ plots and top hit detection")
def summarize_gwas(self, instance: models.AnalysisFileset):
    """Generate "summary" files based on the overall study contents; uses PheWeb loader code"""
    normalized_path = instance.normalized_gwas_path
    qq_path = instance.qq_path

    # Find top hit
    best_row = processors.get_top_hit(normalized_path)
    top_hit = models.RegionView.objects.create(
        gwas=instance.metadata,
        label='Top hit',
        chrom=best_row.chrom,
        start=best_row.pos - 250_000,
        end=best_row.pos + 250_000
    )
    instance.metadata.top_hit_view = top_hit
    instance.metadata.save()

    # Generate files
    processors.generate_qq(normalized_path, qq_path)


@shared_task(bind=True)
@lz_file_prep("Prepare a manhattan plot")
def manhattan_plot(self, instance: models.AnalysisFileset):
    # This is a separate task because it can be quite slow
    normalized_path = instance.normalized_gwas_path
    manhattan_path = instance.manhattan_path
    processors.generate_manhattan(normalized_path, manhattan_path)


@shared_task(bind=True)
def mark_success(self, fileset_id):
    """Notify the owner of a gwas that ingestion has successfully completed"""
    instance = models.AnalysisFileset.objects.get(pk=fileset_id)

    instance.ingest_status = 2
    instance.ingest_complete = timezone.now()
    instance.save()

    # The parent object needs to know which instance is the current newest / best one to display
    metadata = instance.metadata
    metadata.files = instance
    metadata.save()

    send_mail('Results done processing',
              f'Your upload is done processing. Please visit https://{settings.LZ_OFFICIAL_DOMAIN}{metadata.get_absolute_url()} to see the Manhattan plot.',
              'locuszoom-service@umich.edu',
              [metadata.owner.email])


@shared_task(bind=True)
def mark_failure(self, fileset_id):
    """
    Mark a task as failed, and email site admins (for every failure).
    Eventually, we can dial back the error emails a bit.
    """
    instance = models.AnalysisFileset.objects.get(pk=fileset_id)

    logger.exception(f'Ingestion pipeline failed for gwas id: {fileset_id}')
    instance.ingest_status = 1
    instance.ingest_complete = timezone.now()
    instance.save()

    metadata = instance.metadata
    send_mail('Results done processing',
              f'Your upload failed to process. Please visit https://{settings.LZ_OFFICIAL_DOMAIN}{metadata.get_absolute_url()} to see the error logs.',
              'locuszoom-service@umich.edu',
              [metadata.owner.email])

    mail_admins('Results done processing',
                f'Data ingestion failed for gwas id: {metadata.slug}. Please see logs for details.'
    )


def total_pipeline(fileset_id: int):
    """Combine discrete tasks into a total pipeline"""
    return (
        hash_contents.si(fileset_id) |
        normalize_gwas.si(fileset_id) |
        summarize_gwas.si(fileset_id) |
        manhattan_plot.si(fileset_id) |
        mark_success.si(fileset_id)
    ).on_error(mark_failure.si(fileset_id))


@receiver(signals.post_save, sender=models.AnalysisFileset)
def gwas_upload_signal(sender, instance: models.AnalysisFileset = None, created=None, **kwargs):
    """
    Run the ingest pipeline whenever a new record is created in the database

    Thin wrapper to start a celery task.
    """
    # Only run once when model first created.
    # This is a safeguard to prevent infinite recursion from re-saves
    if not created or not instance:
        return

    # Avoid atomic request race condition by only running task once record created
    transaction.on_commit(lambda: total_pipeline(instance.pk).apply_async())

