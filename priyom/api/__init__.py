import teapot

from .shared import *

from . import common_user
from . import anonymous_user
from . import log
from . import stations
from . import formats
from . import alphabets
from . import modulations

@teapot.file_from_directory(
    "/css/",
    "/var/www/docroot/horazont/projects/priyomdb2/resources/css/",
    "f",
    filterfunc=lambda x: x.endswith(".css"))
@router.route(methods={teapot.request.Method.GET})
def css_file(f):
    return teapot.response.Response.file(
        teapot.mime.Type("text", "css").with_charset("utf-8"),
        f)

anonymous_sitemap.label = "Anonymous activities"
anonymous_sitemap.new(
    anonymous_user.anonhome,
    label="Home")
anonymous_sitemap.new(
    stations.view_stations,
    label="View stations")
anonymous_sitemap.new(
    anonymous_user.login,
    label="Log in")

user_sitemap.label = "Common activities"
user_sitemap.new(
    common_user.dash,
    label="Dash")
user_sitemap.new(
    stations.view_stations,
    label="View stations")
user_sitemap.new(
    log.log,
    label="Log TX")
user_sitemap.new(
    common_user.logout,
    label="Sign out")

admin_sitemap.label = "Admin activities"
admin_sitemap.new(
    alphabets.view_alphabets,
    label="Alphabets")
admin_sitemap.new(
    modulations.view_modulations,
    label="Modulations")
admin_sitemap.new(
    formats.view_formats,
    label="Transmission formats")

moderator_sitemap.label = "Moderator activities"

from . import initializer
initializer.create_base_data(Session())
