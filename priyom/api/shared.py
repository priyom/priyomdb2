import binascii

import sqlalchemy
import sqlalchemy.orm

import teapot
import teapot.routing.selectors
import teapot.sqlalchemy
import teapot.templating

import xsltea

import priyom.model

from . import sitemap

__all__ = [
    "xsltea_site",
    "anonymous_sitemap",
    "user_sitemap",
    "admin_sitemap",
    "moderator_sitemap",
    "Session",
    "router"]

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
_xsltea_loader.loader.add_processor(xsltea.ForeachProcessor(allow_unsafe=True))
_xsltea_loader.loader.add_processor(xsltea.ExecProcessor())
_xsltea_loader.loader.add_processor(xsltea.IncludeProcessor())
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
        if "api_session_key" in request.cookie_data:
            try:
                key = request.cookie_data["api_session_key"].pop()
            except ValueError:
                return None
            try:
                session = request.dbsession.query(
                    priyom.model.UserSession).filter(
                        priyom.model.UserSession.session_key == \
                        binascii.a2b_hex(key.encode())).one()
            except sqlalchemy.orm.exc.NoResultFound as err:
                return None

            return session

    def pre_route_hook(self, request):
        super().pre_route_hook(request)
        request.auth = self._reauth(request)

router = _Router()

del _Router