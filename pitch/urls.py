from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("pitches/", views.PitchListView.as_view(), name="pitches"),
]
