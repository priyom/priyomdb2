import abc
import ast
import functools
import logging

import teapot
import teapot.routing.info
import teapot.routing.selectors

import xsltea.processor
import xsltea.exec

from xsltea.namespaces import NamespaceMeta, shared_ns

import priyom.model.user

__all__ = [
    "require_login",
    "require_capability",
    "Capability"]

logger = logging.getLogger(__name__)

# selectors for use with teapot

def raise_missing_auth_error(auth_routable, request, info=""):
    if auth_routable is not None:
        raise teapot.make_redirect_response(
            request, auth_routable)
    else:
        msg = "Not authenticated or not authorized"
        if info:
            msg += ": {}".format(info)
            raise teapot.errors.make_response_error(
                401, msg)

class require_login(teapot.routing.selectors.Selector):
    def __init__(self, *, unauthed_routable=None, **kwargs):
        super().__init__(**kwargs)
        self._unauthed_routable = unauthed_routable

    def select(self, request):
        request = request.original_request
        logger.debug("require_login: %r", request.auth)
        if request.auth.user is None:
            raise_missing_auth_error(
                self._unauthed_routable,
                request,
                info="not logged in")

        return True

    def unselect(self, request):
        return True

class require_capability(teapot.routing.selectors.Selector):
    def __init__(self, *capabilities, unauthed_routable=None, **kwargs):
        super().__init__(**kwargs)
        self._capabilities = set(capabilities)
        self._capabilities.add(Capability.ROOT)
        self._unauthed_routable = unauthed_routable

    def select(self, request):
        request = request.original_request
        logger.debug("require_capability: %s", self._capabilities)

        if not any(request.auth.has_capability(cap)
                   for cap in self._capabilities):
            raise_missing_auth_error(
                self._unauthed_routable,
                request,
                info="missing capability")

        return True

    def unselect(self, request):
        return True

class Capability:
    __init__ = None
    __new__ = None

    # the ROOT capability allows everything. It is a short-circuit in the
    # require_capability decorator. It should not be used directly, except if
    # only users with ROOT are allowed to perform an action
    ROOT = "ROOT"

    CREATE_EVENT = "create-event"
    DELETE_EVENT = "delete-event"
    EDIT_EVENT = "edit-event"
    VIEW_EVENT = "view-event"
    REASSIGN_EVENT = "reassign-event"

    CREATE_MODE = "create-mode"
    DELETE_MODE = "delete-mode"
    EDIT_MODE = "edit-mode"
    VIEW_MODE = "view-mode"

    CREATE_FORMAT = "create-format"
    DELETE_FORMAT = "delete-format"
    EDIT_FORMAT = "edit-format"
    VIEW_FORMAT = "view-format"

    CREATE_STATION = "create-station"
    DELETE_STATION = "delete-station"
    EDIT_STATION = "edit-station"
    VIEW_STATION = "view-station"

    CREATE_ALPHABET = "create-alphabet"
    DELETE_ALPHABET = "delete-alphabet"
    EDIT_ALPHABET = "edit-alphabet"
    VIEW_ALPHABET = "view-alphabet"

    CREATE_USER = "create-user"
    DELETE_USER = "delete-user"
    EDIT_USER = "edit-user"
    VIEW_USER = "view-user"
    EDIT_SELF = "edit-self"

    CREATE_GROUP = "create-group"
    DELETE_GROUP = "delete-group"
    EDIT_GROUP = "edit-group"
    VIEW_GROUP = "view-group"

    LOG = "log"
    LOG_UNMODERATED = "log-unmoderated"

    REVIEW_LOG = "review-log"

class Authorization:
    @classmethod
    def from_session(cls, session):
        return cls(user=session.user)

    @classmethod
    def from_groups(cls, *groups, user=None):
        return cls(user=user, groups=groups)

    def __init__(self, user=None, groups=None):
        if groups is None and user is not None:
            groups = user.groups
        elif groups is None:
            groups = []

        self._user = user
        self._groups = tuple(groups)
        self._capabilities = None

    @property
    def user(self):
        return self._user

    @property
    def groups(self):
        return self._groups

    @property
    def capabilities(self):
        if self._capabilities is not None:
            return self._capabilities

        self._capabilities = priyom.model.user.get_capabilities_from_groups(
            self.groups)

        return self._capabilities

    def _has_capability(self, capability_key):
        if self.user is not None:
            # this is more efficient and uses the database
            return self.user.has_capability(capability_key)

        return capability_key in self.capabilities

    def has_capability(self, capability_key, root_override=True):
        result = self._has_capability(capability_key)
        if root_override and not result:
            return self._has_capability(Capability.ROOT)
        return result

    def has_group(self, group_name):
        if self.user is not None:
            return self.user.has_group(group_name)

        return priyom.model.user.get_has_group_from_groups(
            self.groups, group_name)

class AuthProcessor(xsltea.processor.TemplateProcessor):
    class xmlns(metaclass=NamespaceMeta):
        xmlns = "https://xmlns.zombofant.net/xsltea/auth"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.globalhooks = [self.provide_vars]
        self.attrhooks = {
            (str(shared_ns), "if", str(self.xmlns), "cap"): [self.cond_cap],
            (str(shared_ns), "if", str(self.xmlns), "login"): [self.cond_login],
            (str(shared_ns), "if", str(self.xmlns), "group"): [self.cond_group],
            (str(shared_ns), "case", str(self.xmlns), "cap"): [self.cond_cap],
            (str(shared_ns), "case", str(self.xmlns), "login"): [self.cond_login],
            (str(shared_ns), "case", str(self.xmlns), "group"): [self.cond_group],
        }
        self.elemhooks = {}

    def _access_auth(self, template, sourceline):
        return ast.Attribute(
            template.ast_get_request(sourceline),
            "auth",
            ast.Load(),
            lineno=sourceline,
            col_offset=0)

    def _build_capability_condition(self, auth_ast, capability_key, sourceline):
        return ast.Call(
            ast.Attribute(
                auth_ast,
                "has_capability",
                ast.Load(),
                lineno=sourceline,
                col_offset=0),
            [ # arguments
                ast.Str(
                    getattr(Capability, capability_key),
                    lineno=sourceline,
                    col_offset=0),
            ],
            [],
            None,
            None,
            lineno=sourceline,
            col_offset=0)

    def _build_login_condition(self, auth_ast, logged_in, sourceline):
        return ast.Compare(
            ast.Attribute(
                auth_ast,
                "user",
                ast.Load(),
                lineno=sourceline,
                col_offset=0),
            [
                ast.IsNot() if logged_in else ast.Is()
            ],
            [
                ast.Name(
                    "None",
                    ast.Load(),
                    lineno=sourceline,
                    col_offset=0)
            ],
            lineno=sourceline,
            col_offset=0)

    def _build_group_condition(self, auth_ast, group_key, sourceline):
        return ast.Call(
            ast.Attribute(
                auth_ast,
                "has_group",
                ast.Load(),
                lineno=sourceline,
                col_offset=0),
            [ # arguments
                ast.Str(
                    getattr(priyom.model.user.Group, group_key),
                    lineno=sourceline,
                    col_offset=0),
            ],
            [],
            None,
            None,
            lineno=sourceline,
            col_offset=0)

    def cond_cap(self, template, elem, key, value, context):
        sourceline = elem.sourceline or 0
        auth_ast = self._access_auth(template, sourceline)
        return [], [], None, self._build_capability_condition(
            auth_ast, value, sourceline), []

    def cond_login(self, template, elem, key, value, context):
        sourceline = elem.sourceline or 0
        auth_ast = self._access_auth(template, sourceline)
        return [], [], None, self._build_login_condition(
            auth_ast,
            value.lower() in {"true", "yes", "1"},
            sourceline), []

    def cond_group(self, template, elem, key, value, context):
        sourceline = elem.sourceline or 0
        auth_ast = self._access_auth(template, sourceline)
        return [], [], None, self._build_group_condition(
            auth_ast,
            value,
            sourceline), []

    def provide_vars(self, template, tree, context):
        precode = [
            ast.Assign(
                [
                    ast.Name(
                        "Capability",
                        ast.Store(),
                        lineno=0,
                        col_offset=0),
                ],
                template.ast_get_stored(
                    template.store(Capability),
                    0),
                lineno=0,
                col_offset=0
            )
        ]

        return precode, []
