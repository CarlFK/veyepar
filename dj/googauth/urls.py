from django.urls import path
from . import views

urlpatterns = [
    path('init/', views.goog_start, name='google_permission'),
    path('redirect/', views.goog_redirect, name='google_redirect')
]
