from django.urls import include, path, re_path
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'csp', views.CSPViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    path(r'', include(router.urls)),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
