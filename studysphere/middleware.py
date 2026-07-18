from django.conf import settings
from django.shortcuts import render

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.MAINTENANCE_MODE:
            if not request.path.startswith('/admin/'):
                return render(request, 'errors/503.html', status=503)
        return self.get_response(request)