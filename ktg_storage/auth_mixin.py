from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny


class ApiAuthMixin:
    def get_permissions(self):
        """
        Dynamically set permissions based on ALLOW_AUTHENTICATION setting.

        Returns:
            list: A list of permission classes to apply to the view.
        """
        allow_authentication = getattr(settings, 'ALLOW_AUTHENTICATION', True)

        return [IsAuthenticated()] if allow_authentication else [AllowAny()]
