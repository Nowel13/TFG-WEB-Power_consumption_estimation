from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("uploads", views.upload_processed_files, name="uploads"),
    path("delete", views.delete, name="delete"),
    path("processed", views.process_data, name="processed"),
    path("apply_model", views.apply_model, name="apply_model"),
    path("results", views.results, name="results"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)