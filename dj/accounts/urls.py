#  accounts/views.py

from django.conf.urls.defaults import url, patterns
from django.contrib.auth import views as auth_views

# django-registration default urls
urlpatterns = patterns(
    '',
    url(r'^login$',
        auth_views.login,
        {'template_name': 'accounts/login.html'},
        name='auth_login'),
        )

