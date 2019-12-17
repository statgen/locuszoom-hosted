import functools
import os

from celery.utils.log import get_task_logger
from celery import shared_task
from django.conf import settings
from django.core.mail import mail_admins, send_mail
from django.db.models import signals
from django.db import transaction
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from zorp import (
    parsers,
    sniffers,
    exceptions as z_exc
)

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
            except (exceptions.UnexpectedIngestException, Exception) as e:
                message += '[failure][{}] An error prevented this step from completing\n'.format(
                    timezone.now().replace(microsecond=0).isoformat())
                message += str(e) + '\n'
                # If this task failed, terminate subsequent tasks in the chain and notify the user
                # If we did not do this, the exception would bubble up to sentry, even if it should have been handled
                # TODO: In the future, we can make this handling more fine-grained (eg log totally unexpected problems
                #   to sentry, while swallowing normal things like validation)
                logger.exception('Ingestion failed due to an error')
                self.request.chain = None
                mark_failure.si(fileset_id).apply_async()
            finally:
                with open(log_path, 'a+') as f:
                    f.write(message)
        return inner
    return decorator


@shared_task(bind=True)
@lz_file_prep("Calculate SHA256")
def hash_contents(self, instance: models.AnalysisFileset):
    """Store a unique hash of the file contents"""
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

    parser = parsers.GenericGwasLineParser(**parser_options)
    reader = sniffers.guess_gwas_generic(src_path, parser=parser, skip_errors=True)

    is_valid = False
    try:
        is_valid = validators.standard_gwas_validator.validate(src_path, reader)
    except z_exc.TooManyBadLinesException as e:
        raise e
    else:
        logger.info('GWAS file contents successfully validated')
    finally:
        # Always write a log entry, no matter what
        with open(log_path, 'a+') as f:
            for n, reason, _ in reader.errors:
                f.write('Excluded row {} from output due to parse error: {}\n'.format(n, reason))
            if is_valid:
                f.write('[success] The GWAS file passed validation. Read the logs carefully, in case any specific lines failed to parse.\n')  # noqa
            else:
                f.write('[failure] Could not create normalized GWAS file.\n')

    if not is_valid:
        logger.info(f"Could not load GWAS '{src_path}' because contents failed to validate")
        raise exceptions.ValidationException(f'Validation failed for study ID {instance.metadata.slug}')

    # For now the writer expects a temp file name, and it creates the .gz version internally
    tmp_normalized_path = dest_path.replace('.txt.gz', '.txt')
    processors.normalize_contents(reader, tmp_normalized_path)


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
    metadata = instance.metadata
    normalized_path = instance.normalized_gwas_path
    manhattan_path = instance.manhattan_path
    processors.generate_manhattan(metadata.build, normalized_path, manhattan_path)


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

    # TODO: Render this as a nicer-looking template
    log_url = reverse('gwas:gwas-ingest-log', kwargs={'slug': metadata.slug})
    send_mail('[locuszoom] Upload succeeded',
              f'Your upload is done processing. Please visit https://{settings.LZ_OFFICIAL_DOMAIN}{metadata.get_absolute_url()} to see the Manhattan plot and begin exploring regions of your data.\nBe sure to review the ingest logs for any warnings: https://{settings.LZ_OFFICIAL_DOMAIN}{log_url}',  # noqa
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
    log_url = reverse('gwas:gwas-ingest-log', kwargs={'slug': metadata.slug})
    send_mail('[locuszoom] Upload failed',
              f'Your upload failed to process. Please review the ingest logs for warnings and error messages: https://{settings.LZ_OFFICIAL_DOMAIN}{log_url}\nOr visit the upload page to change settings: https://{settings.LZ_OFFICIAL_DOMAIN}{metadata.get_absolute_url()}',  # noqa
              'locuszoom-service@umich.edu',
              [metadata.owner.email])

    mail_admins(
        '[locuszoom-service] Ingest error',
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
