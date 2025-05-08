import logging
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from locuszoom_plotting_service.gwas import models as lz_models
from locuszoom_plotting_service.gwas import util

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Command to delete a GWAS study by slug/ID.
    This command will delete the associated files and mark the study as deleted in the database.

    Example usage with docker:
      docker compose -f <your-config.yml> run --rm django python manage.py delete_gwas <slug ID>
    """
    help = 'Delete a GWAS study by slug/ID'

    def add_arguments(self, parser):
        parser.add_argument('slug', help='The slug of the GWAS study to delete')
        parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')

    def handle(self, *args, **options):
        slug = options['slug']
        force = options['force']
        
        try:
            gwas = lz_models.AnalysisInfo.objects.all_active().get(slug=slug)
        except lz_models.AnalysisInfo.DoesNotExist:
            raise CommandError(f'GWAS study with slug "{slug}" not found or already deleted')
        
        if not force:
            confirm = input(f'Are you sure you want to delete GWAS study "{gwas.label}" (ID: {gwas.id})? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Deletion aborted.'))
                return
        
        try:
            # First part: Delete files (same as in GwasDelete.delete)
            for fileset in gwas.analysisfileset_set.all():
                target_path = util.get_study_folder(fileset, absolute_path=True)
                logger.info('Command has requested that we delete media folder: {}'.format(target_path))
                if not target_path or not os.path.isdir(target_path) or \
                        target_path.strip('/') == settings.MEDIA_ROOT.strip('/'):
                    # Guard against some malformed path bugs that would be really awkward to explain
                    raise Exception('Cannot find the data requested for deletion')

                shutil.rmtree(target_path)
            
            # Second part: Simply call delete() on the model
            # Since AnalysisInfo is a SoftDeletableModel, this will set is_removed=True
            # and handle all appropriate signals
            gwas.delete()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted GWAS study "{gwas.label}" (ID: {gwas.id})'))
            
        except Exception as e:
            raise CommandError(f'Failed to delete GWAS study: {e}')