from django.conf import settings


def common_settings(request):
    """
    Exports a selection of Django settings variables to templates
    """
    return {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'SENTRY_DSN_FRONTEND': settings.SENTRY_DSN_FRONTEND,
    }
