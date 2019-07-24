# Generated by Django 2.0.13 on 2019-07-23 19:03

from django.db import migrations, models
import locuszoom_plotting_service.base.util
import locuszoom_plotting_service.gwas.models


class Migration(migrations.Migration):

    dependencies = [
        ('gwas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisinfo',
            name='slug',
            field=models.SlugField(default=locuszoom_plotting_service.base.util._generate_slug, editable=False, help_text='The external facing identifier for this record', max_length=6, unique=True),
        ),
        migrations.AlterField(
            model_name='analysisfileset',
            name='pipeline_path',
            field=models.CharField(default=locuszoom_plotting_service.gwas.models._pipeline_folder, help_text='Internal use only: path to folder of ingested data. Value auto-set.', max_length=32),
        ),
    ]