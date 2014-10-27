import binascii
import logging

import pytz

import sqlalchemy
import sqlalchemy.orm

import teapot
import teapot.routing
import teapot.routing.selectors
import teapot.sqlalchemy
import teapot.templating

import xsltea
import xsltea.i18n

import priyom.config
import priyom.model

from . import sitemap, sortable_table, auth, svgicon

__all__ = [
    "xsltea_site",
    "user_sitemap",
    "admin_sitemap",
    "moderator_sitemap",
    "Session",
    "router"]

logger = logging.getLogger(__name__)

source = teapot.templating.FileSystemSource(
    priyom.config.get_data_path("templates"))

# setup localization support

textdb = xsltea.i18n.TextDatabase(
    fallback_locale="en_GB",
    fallback_mode="key")
textdb.load_all(priyom.config.get_data_path("l10n"))

# setup sitemap root

sitemap_root = sitemap.Node()

user_sitemap = sitemap_root.new(
    None,
    label="Common activities")
moderator_sitemap = sitemap_root.new(
    None,
    label="Moderator activities")
admin_sitemap = sitemap_root.new(
    None,
    label="Admin activities")

# setup xsltea transforms

sprites = "/img/sprites.svg"

_transform_loader = xsltea.TransformLoader(source)

_xsltea_loader = xsltea.Pipeline()
_xsltea_loader.loader = xsltea.XMLTemplateLoader(source)
_xsltea_loader.loader.add_processor(xsltea.BranchingProcessor())
_xsltea_loader.loader.add_processor(xsltea.ForeachProcessor(
    safety_level=xsltea.SafetyLevel.unsafe))
_xsltea_loader.loader.add_processor(xsltea.FormProcessor(
    errorclass="error",
    safety_level=xsltea.SafetyLevel.unsafe))
_xsltea_loader.loader.add_processor(sortable_table.SortableTableProcessor(
    active_column_class="order-by",
    order_indicator_class="order-indicator"))
_xsltea_loader.loader.add_processor(xsltea.ExecProcessor())
_xsltea_loader.loader.add_processor(xsltea.IncludeProcessor())
_xsltea_loader.loader.add_processor(xsltea.FunctionProcessor(
    safety_level=xsltea.SafetyLevel.unsafe))
_xsltea_loader.loader.add_processor(auth.AuthProcessor())
_xsltea_loader.loader.add_processor(svgicon.SVGIconProcessor(
    sprites,
    default_viewbox="0 0 32 32"))
_xsltea_loader.loader.add_processor(xsltea.i18n.I18NProcessor(
    textdb,
    safety_level=xsltea.SafetyLevel.unsafe))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "user", user_sitemap,
    sprites
))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "moderator", moderator_sitemap,
    sprites
))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "admin", admin_sitemap,
    sprites
))
_xsltea_loader.loader.add_processor(sitemap.CrumbsProcessor(
    sitemap_root
))
_xsltea_loader.loader.add_processor(xsltea.SortableTableProcessor(
    active_column_class="order-by",
    order_indicator_class="order-indicator",
    safety_level=xsltea.SafetyLevel.unsafe
))

_xsltea_website_output = xsltea.XHTMLPipeline()

xsltea_site = xsltea.Pipeline(
    chain_from=_xsltea_loader,
    chain_to=_xsltea_website_output)
xsltea_site.local_transforms.append(_transform_loader.load_transform(
    "default.xsl"))

del _xsltea_website_output
del _xsltea_loader

_dbengine = sqlalchemy.create_engine(
    priyom.config.database_url,
    echo=False,
    encoding="utf8",
    convert_unicode=True)
Session = sqlalchemy.orm.sessionmaker(bind=_dbengine)
del _dbengine

@xsltea_site.with_template("internal_server_error.xml")
def internal_server_error(request: teapot.request.Request,
                          exc_info):
    yield teapot.response.Response(None, response_code=500)

    _, exc, tb = exc_info

    yield ({
        "exc": exc,
        "tb": tb
    }, {})

# main router

class _Router(teapot.sqlalchemy.SessionMixin, teapot.routing.Router):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sessionmaker=Session, **kwargs)

    def handle_internal_server_error(self, request, exc_info):
        request.current_routable = internal_server_error

        ctx = teapot.routing.Context.from_request(request)
        selectors = teapot.routing.getrouteinfo(internal_server_error).selectors
        for selector in selectors:
            selector.select(ctx)

        yield from internal_server_error(*ctx.args,
                                         exc_info=exc_info,
                                         **ctx.kwargs)

    def _reauth(self, request):
        from .auth import Authorization

        if "api_session_key" in request.cookie_data:
            try:
                key = request.cookie_data["api_session_key"].pop()
            except ValueError:
                return None
            try:
                session = request.dbsession.query(
                    priyom.model.UserSession
                ).filter(
                    priyom.model.UserSession.session_key == \
                    binascii.a2b_hex(key.encode())
                ).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                pass
            else:
                return Authorization.from_session(session)

        try:
            anon_group = request.dbsession.query(
                priyom.model.Group
            ).filter(
                priyom.model.Group.name == priyom.model.Group.ANONYMOUS
            ).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            logger.warn(
                "No anonymous group found, non-logged-in users will have no"
                " privilegues. To silence this warning, create a group without"
                " privilegues called '%s'.",
                priyom.model.Group.ANONYMOUS)
            return Authorization()
        else:
            return Authorization.from_groups(anon_group)

    def pre_route_hook(self, request):
        super().pre_route_hook(request)
        request.auth = self._reauth(request)

        if request.auth.user is not None:
            request.localizer = textdb.get_localizer(
                request.auth.user.locale,
                pytz.timezone(request.auth.user.timezone))

        class Foo:
            auth = request.auth

            def __str__(self):
                return "authorized with groups {} and capabilities {}".format(
                    ", ".join(map(str, self.auth.groups)),
                    ", ".join(map(str, self.auth.capabilities)))

        logger.info(Foo())

router = _Router()

del _Router
