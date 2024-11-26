from django.conf import settings
from rest_framework.permissions import IsAuthenticated


class ApiAuthMixin:
    def get_permissions(self):
        allow_authentication = getattr(settings, 'ALLOW_AUTHENTICATION', True)

        if allow_authentication:
            return [IsAuthenticated()]
        else:
            return []
