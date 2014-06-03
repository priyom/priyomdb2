import os

import teapot

import priyom.config

from .shared import *

from . import common_user
from . import anonymous_user
from . import log
from . import stations
from . import events
from . import formats
from . import alphabets
from . import modes

mimetypes = {
    ".ttf": teapot.mime.Type("application", "x-font-ttf"),
    ".eot": teapot.mime.Type("application", "vnd.ms-fontobject"),
    ".woff": teapot.mime.Type("application", "octet-stream"),
    ".svg": teapot.mime.Type("image", "svg+xml"),
    None: teapot.mime.Type("application", "octet-stream")
}

@teapot.file_from_directory(
    "/css/",
    priyom.config.css_path,
    "f",
    filterfunc=lambda x: x.endswith(".css"))
@router.route(methods={teapot.request.Method.GET})
def css_file(f):
    return teapot.response.Response.file(
        teapot.mime.Type("text", "css").with_charset("utf-8"),
        f)


@teapot.file_from_directory(
    "/img/",
    priyom.config.img_path,
    "f")
@router.route(methods={teapot.request.Method.GET})
def img_file(f):
    _, ext = os.path.splitext(f.name)

    mimetype = mimetypes.get(ext, mimetypes[None])

    return teapot.response.Response.file(mimetype, f)

anonymous_sitemap.label = "Anonymous activities"
anonymous_sitemap.new(
    anonymous_user.anonhome,
    label="Home")
anonymous_sitemap.new(
    stations.view_stations,
    label="Stations")
anonymous_sitemap.new(
    events.view_events,
    label="Events")
anonymous_sitemap.new(
    anonymous_user.login,
    label="Sign in")

user_sitemap.label = "Common activities"
user_sitemap.new(
    common_user.dash,
    label="Dash")
user_sitemap.new(
    stations.view_stations,
    label="Stations")
user_sitemap.new(
    events.view_events,
    label="Events")
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
    modes.view_modes,
    label="Modes")
admin_sitemap.new(
    formats.view_formats,
    label="Transmission formats")

moderator_sitemap.label = "Moderator activities"

from . import initializer
initializer.create_base_data(Session())
