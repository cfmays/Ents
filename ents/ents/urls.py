"""ents URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from . import settings


admin.site.site_header = "Enrichments Admin"
admin.site.site_title = "Enrichments Admin Portal"
admin.site.index_title = "Welcome to Enrichments Admin Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index, name='index'),
    path('create/', views.EnrichmentUploadView, name='createView'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('password/', auth_views.PasswordChangeView.as_view(
        template_name='password_change.html', success_url=reverse_lazy('password_change_done')), name='password_change'),
    path('password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('ajax_get_image_url', views.ajax_get_image_url, name='ajax_get_image_url'),
    path('ajax_load_searchstring_items', views.ajax_load_searchstring_items, name='ajax_load_searchstring_items'),
    path('zoo/', include('zoo.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
