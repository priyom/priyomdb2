import binascii
import logging
import os

import sqlalchemy
import sqlalchemy.orm

import teapot
import teapot.request
import teapot.routing
import teapot.routing.selectors
import teapot.templating
import teapot.mime

import xsltea

import priyom.model
import priyom.model.user

from . import sitemap

source = teapot.templating.FileSystemSource(
    "/var/www/docroot/horazont/projects/priyomdb2/resources/templates/")

# setup sitemap root

anonymous_sitemap = sitemap.Node()
user_sitemap = sitemap.Node()
moderator_sitemap = sitemap.Node()
admin_sitemap = sitemap.Node()

# setup xsltea transforms

_transform_loader = xsltea.TransformLoader(source)

_xsltea_loader = xsltea.Pipeline()
_xsltea_loader.loader = xsltea.XMLTemplateLoader(source)
_xsltea_loader.loader.add_processor(xsltea.ForeachProcessor)
_xsltea_loader.loader.add_processor(xsltea.ExecProcessor)
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "anonymous", anonymous_sitemap
))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "user", user_sitemap
))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "moderator", moderator_sitemap
))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "admin", admin_sitemap
))

_xsltea_website_output = xsltea.XHTMLPipeline()

xsltea_site = xsltea.Pipeline(
    chain_from=_xsltea_loader,
    chain_to=_xsltea_website_output)
xsltea_site.local_transforms.append(_transform_loader.load_transform(
    "default.xsl"))

del _xsltea_website_output
del _xsltea_loader

dbengine = sqlalchemy.create_engine(
    "mysql+mysqlconnector://priyom2@localhost/priyom2?charset=utf8",
    echo=False,
    encoding="utf8",
    convert_unicode=True)
priyom.model.Base.metadata.create_all(dbengine)
dbsession = sqlalchemy.orm.sessionmaker(bind=dbengine)()

# main router

class Router(teapot.routing.Router):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def _reauth(self, request):
        if "api_session_key" in request.cookie_data:
            try:
                key = request.cookie_data["api_session_key"].pop()
            except ValueError:
                return None
            try:
                session = dbsession.query(
                    priyom.model.UserSession).filter(
                        priyom.model.UserSession.session_key == \
                        binascii.a2b_hex(key.encode())).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                return None

            return session

    def pre_route_hook(self, request):
        request.auth = self._reauth(request)

router = Router()

# selectors for use with teapot

class require_login(teapot.routing.selectors.Selector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _raise_missing_auth_error(self):
        raise teapot.errors.make_response_error(
            401, "Not authenticated or not authorized")

    def select(self, request):
        request = request.original_request
        logging.debug("require_login: %r", request.auth)
        if request.auth is None:
            self._raise_missing_auth_error()
        if not hasattr(request.auth, "user"):
            self._raise_missing_auth_error()

        return True

    def unselect(self, request):
        return True

class require_capability(require_login):
    def __init__(self, capability, **kwargs):
        super().__init__(**kwargs)
        self._capability = capability

    def select(self, request):
        if not super().select(request):
            return False
        request = request.original_request
        logging.debug("require_capability: %s", self._capability)

        user = request.auth.user
        caps = set(usercap.key for usercap in user.capabilities)
        if not self._capability in caps:
            self._raise_missing_auth_error()

        return True

@teapot.file_from_directory(
    "/css/",
    "/var/www/docroot/horazont/projects/priyomdb2/mocks/css/",
    "f",
    filterfunc=lambda x: x.endswith(".css"))
@router.route(methods={teapot.request.Method.GET})
def css_file(f):
    return teapot.response.Response.file(
        teapot.mime.Type("text", "css").with_charset("utf-8"),
        f)

@require_login()
@router.route("/", methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("dash.xml")
def dash(request: teapot.request.Request):
    yield teapot.response.Response(None)
    transform_args = {
        "version": "devel"
    }
    template_args = dict(transform_args)
    template_args["auth"] = request.auth
    yield (template_args, transform_args)

@router.route("/", methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("home.xml")
def anonhome(request: teapot.request.Request):
    yield teapot.response.Response(None)
    transform_args = {
        "version": "devel"
    }
    template_args = dict(transform_args)
    yield (template_args, transform_args)

@require_login()
@router.route("/logout", methods={teapot.request.Method.GET})
def logout(request: teapot.request.Request):
    response = teapot.make_redirect_response(request, anonhome)
    response.cookies["api_session_key"] = ""
    response.cookies["api_session_key"]["Expires"] = 1
    return response

@router.route("/login", methods={teapot.request.Method.GET}, order=1)
@xsltea_site.with_template("login.xml")
def login_GET():
    yield teapot.response.Response(None)
    yield ({}, {})

@teapot.postarg("name", "loginname")
@teapot.postarg("password", "password")
@router.route("/login", methods={teapot.request.Method.POST}, order=1)
@xsltea_site.with_template("login.xml")
def login_POST(loginname, password, request: teapot.request.Request):
    error = False
    error_msg = None
    try:
        user = dbsession.query(
            priyom.model.User).filter(
                priyom.model.User.loginname == loginname).one()
        print(user)
        if not priyom.model.user.verify_password(
                user.password_verifier,
                password):
            error = True
    except sqlalchemy.orm.exc.NoResultFound as err:
        error = True
    except (LookupError, ValueError) as err:
        error = True
        # FIXME: stop leaking information about the existing user here, even
        # if it is broken
        error_msg = "Internal authentication error"

    if error:
        if error_msg is None:
            error_msg = "Unknown user name or invalid password"
        yield teapot.response.Response(None, response_code=401)
        yield (
            {
                "error": error_msg
            },
            {})

    session = priyom.model.UserSession(user)
    dbsession.add(session)
    dbsession.commit()

    # FIXME: login!
    response = teapot.make_redirect_response(request, dash)
    response.cookies["api_session_key"] = binascii.b2a_hex(
        session.session_key).decode()
    response.cookies["api_session_key"]["httponly"] = True

    yield response


anonymous_sitemap.label = "Anonymous activities"
anonymous_sitemap.new(
    anonhome,
    label="Home")
anonymous_sitemap.new(
    login_GET,
    label="Log in")

user_sitemap.label = "Common activities"
user_sitemap.new(
    dash,
    label="Dash")
user_sitemap.new(
    logout,
    label="Log out")

admin_sitemap.label = "Admin activities"
moderator_sitemap.label = "Moderator activities"

from . import initializer
initializer.create_test_data(dbsession)
