"""
Add an admin site for this project, and also perform project-wide customizations
"""
from django.contrib import admin

from allauth.socialaccount.models import SocialToken

from .models import AnalysisInfo


# Certain other apps in the site register models that we don't want exposed to a public admin UI. For example,
#  social auth user tokens. We'll manually de-register them in an file that is loaded after allauth
admin.site.unregister([SocialToken])

# We may want to re-enable this in the future, but for now this is a powerful action and we will delete it
admin.site.disable_action('delete_selected')

# Add custom UI: view analysis info objects, ingest status, maybe a default sort order
class AnalysisInfoAdmin(admin.ModelAdmin):
    list_display = ['created', 'owner', 'label', 'ingest_status']
    list_select_related = ['files', 'owner']
    ordering = ['created']

    actions = ['rerun_ingest']

    def rerun_ingest(self, request, queryset):
        for obj in queryset:
            # An admin can trigger this without any permissions checks
            obj.rerun_ingest()

        # TODO: Use sparingly as this sends an email to all the users!!
        self.message_user(
            request,
            '{} studies have been resubmitted and users have been notified'.format(queryset.count())
        )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion on the individual-item page
        # This is because a) Additional cleanup is required for this delete (it's more than a model flag), and
        #   b) users, not admins, should dictate removal of their data. (at least until we better understand removal
        #   requests)
        return False

admin.site.register(AnalysisInfo, AnalysisInfoAdmin)
