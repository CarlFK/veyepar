#  accounts/views.py

# from django.conf.urls import url
from django.urls import include, re_path

from accounts.views import logax

# django-registration default urls
urlpatterns = [
    re_path(r'^login/',
        logax,
        name='auth_login',
        ),
]

