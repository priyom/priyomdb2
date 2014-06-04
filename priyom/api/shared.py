import binascii
import logging

import sqlalchemy
import sqlalchemy.orm

import teapot
import teapot.routing.selectors
import teapot.sqlalchemy
import teapot.templating

import xsltea

import priyom.config
import priyom.model

from . import sitemap, sortable_table, auth, i18n, svgicon

__all__ = [
    "xsltea_site",
    "anonymous_sitemap",
    "user_sitemap",
    "admin_sitemap",
    "moderator_sitemap",
    "Session",
    "router"]

logger = logging.getLogger(__name__)

source = teapot.templating.FileSystemSource(
    "/var/www/docroot/horazont/projects/priyomdb2/resources/templates/")

# setup localization support

textdb = i18n.TextDB(fallback_locale="en_GB")
textdb.load_all(priyom.config.l10n_path)

# setup sitemap root

anonymous_sitemap = sitemap.Node()
user_sitemap = sitemap.Node()
moderator_sitemap = sitemap.Node()
admin_sitemap = sitemap.Node()

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
_xsltea_loader.loader.add_processor(xsltea.FunctionProcessor())
_xsltea_loader.loader.add_processor(auth.AuthProcessor())
_xsltea_loader.loader.add_processor(svgicon.SVGIconProcessor(
    sprites,
    default_viewbox="0 0 32 32"))
_xsltea_loader.loader.add_processor(i18n.I18NProcessor(
    textdb,
    safety_level=xsltea.SafetyLevel.unsafe))
_xsltea_loader.loader.add_processor(sitemap.SitemapProcessor(
    "anonymous", anonymous_sitemap,
    sprites
))
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

_xsltea_website_output = xsltea.XHTMLPipeline()

xsltea_site = xsltea.Pipeline(
    chain_from=_xsltea_loader,
    chain_to=_xsltea_website_output)
xsltea_site.local_transforms.append(_transform_loader.load_transform(
    "default.xsl"))

del _xsltea_website_output
del _xsltea_loader

_dbengine = sqlalchemy.create_engine(
    "mysql+mysqlconnector://priyom2@localhost/priyom2?charset=utf8",
    echo=False,
    encoding="utf8",
    convert_unicode=True)
priyom.model.Base.metadata.create_all(_dbengine)
Session = sqlalchemy.orm.sessionmaker(bind=_dbengine)
del _dbengine

# main router

class _Router(teapot.sqlalchemy.SessionMixin, teapot.routing.Router):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, sessionmaker=Session, **kwargs)

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

        class Foo:
            auth = request.auth

            def __str__(self):
                return "authorized with groups {} and capabilities {}".format(
                    ", ".join(map(str, self.auth.groups)),
                    ", ".join(map(str, self.auth.capabilities)))

        logger.info(Foo())

router = _Router()

del _Router
