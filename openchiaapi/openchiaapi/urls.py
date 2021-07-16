from django.urls import path, re_path, include
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


router = routers.DefaultRouter()

schema_view = get_schema_view(
    openapi.Info(
        title="API",
        default_version='v1.0',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('api/v1.0/', include('api.urls', namespace='v1.0')),
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^api/doc(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^api/doc/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + router.urls
