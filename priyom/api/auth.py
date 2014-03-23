import logging

import teapot
import teapot.routing.selectors

from .shared import *

__all__ = [
    "require_login",
    "require_capability"]

logger = logging.getLogger(__name__)

# selectors for use with teapot

class require_login(teapot.routing.selectors.Selector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._auth_routable = None

    def _raise_missing_auth_error(self, request):
        if self._auth_routable is not None:
            raise teapot.make_redirect_response(
                request, self._auth_routable)
        else:
            raise teapot.errors.make_response_error(
                401, "Not authenticated or not authorized")

    def select(self, request):
        request = request.original_request
        logger.debug("require_login: %r", request.auth)
        if request.auth is None:
            self._raise_missing_auth_error(request)
        if not hasattr(request.auth, "user"):
            self._raise_missing_auth_error(request)

        return True

    def unselect(self, request):
        return True

class require_capability(require_login):
    def __init__(self, *capabilities, **kwargs):
        super().__init__(**kwargs)
        self._capabilities = capabilities

    def select(self, request):
        if not super().select(request):
            return False
        request = request.original_request
        logger.debug("require_capability: %s", self._capabilities)

        if not any(request.auth.user.has_capability(cap)
                   for cap in self._capabilities):
            self._raise_missing_auth_error(request)

        return True
