import teapot

from .shared import *

from . import common_user
from . import anonymous_user

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

anonymous_sitemap.label = "Anonymous activities"
anonymous_sitemap.new(
    anonymous_user.anonhome,
    label="Home")
anonymous_sitemap.new(
    anonymous_user.login,
    label="Log in")

user_sitemap.label = "Common activities"
user_sitemap.new(
    common_user.dash,
    label="Dash")
user_sitemap.new(
    common_user.logout,
    label="Log out")

admin_sitemap.label = "Admin activities"
moderator_sitemap.label = "Moderator activities"

from . import initializer
initializer.create_test_data(dbsession)
