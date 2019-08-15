from django.conf import settings # import the settings file

def common_settings(request):
    """
    Exports a selection of Django settings variables to templates
    """
    return {'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID}
