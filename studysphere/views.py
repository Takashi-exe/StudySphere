from django.shortcuts import render

def root_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'admin_dashboard.html')
        else:
            friends = request.user.profile.friends.exclude(id=request.user.id)
            groups = request.user.study_groups.all()
            return render(request, 'dashboard.html', {'friends': friends, 'groups': groups})
    else:
        return render(request, 'landing.html')

def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)

def custom_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)