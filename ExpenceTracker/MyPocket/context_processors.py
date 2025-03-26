from django.conf import settings

def site_settings(request):
    """Make important settings available in templates"""
    return {
        'SITE_NAME': settings.SITE_NAME,
        'MAX_UPLOAD_SIZE_MB': settings.MAX_UPLOAD_SIZE / 1024 / 1024,
    }