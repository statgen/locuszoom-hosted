"""Querysets and managers that mediate interaction between the model and the database"""
from model_utils.managers import SoftDeletableQuerySet


class AnalysisInfoQuerySet(SoftDeletableQuerySet):
    """
    Define a set of chainable, predefined filters that can be applied to any queries on this model
    """
    def public(self):
        """Studies that are visible to anyone"""
        return self.all_active().filter(is_public=True)

    def ingested(self):
        """Studies that have completed ingestion successfully, and are ready to be shown in, eg, public listings"""
        return self.all_active().filter(files__isnull=False)

    def all_active(self):
        """
        This app uses soft deletes, so users will almost always want to use this helper rather than `objects.all()`
        """
        return self.filter(is_removed=False)


AnalysisInfoManager = AnalysisInfoQuerySet.as_manager()

