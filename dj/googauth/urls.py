from django.urls import path
from . import views

urlpatterns = [
    path('init/', views.goog_init),
    path('redirect/', views.goog_redirect),
]
