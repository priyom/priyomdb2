import os

import teapot

import priyom.config

from .shared import *

from . import log
from . import stations
from . import events
from . import formats
from . import alphabets
from . import modes
from . import dash
from . import login
from . import users

mimetypes = {
    ".ttf": teapot.mime.Type("application", "x-font-ttf"),
    ".eot": teapot.mime.Type("application", "vnd.ms-fontobject"),
    ".woff": teapot.mime.Type("application", "octet-stream"),
    ".svg": teapot.mime.Type("image", "svg+xml"),
    ".png": teapot.mime.Type("image", "png"),
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
    dash.dash,
    label="Home",
    svgicon=svgicon.SVGIcon("icon-bars"))
anonymous_sitemap.new(
    stations.view_stations,
    label="Stations",
    svgicon=svgicon.SVGIcon("icon-podcast"))
anonymous_sitemap.new(
    events.view_events,
    label="Events",
    svgicon=svgicon.SVGIcon("icon-info-circle"))
anonymous_sitemap.new(
    login.login,
    label="Sign in",
    svgicon=svgicon.SVGIcon("icon-enter"))

user_sitemap.label = "Common activities"
user_sitemap.new(
    dash.dash,
    label="Dash",
    svgicon=svgicon.SVGIcon("icon-bars"))
user_sitemap.new(
    stations.view_stations,
    label="Stations",
    svgicon=svgicon.SVGIcon("icon-podcast"))
user_sitemap.new(
    events.view_events,
    label="Events",
    svgicon=svgicon.SVGIcon("icon-info-circle"))
user_sitemap.new(
    log.log,
    label="Log TX",
    svgicon=svgicon.SVGIcon("icon-microphone"))
user_sitemap.new(
    users.edit_self,
    label="My account",
    svgicon=svgicon.SVGIcon("icon-user"))
user_sitemap.new(
    login.logout,
    label="Sign out",
    svgicon=svgicon.SVGIcon("icon-exit"))

admin_sitemap.label = "Admin activities"
admin_sitemap.new(
    alphabets.view_alphabets,
    label="Alphabets",
    svgicon=svgicon.SVGIcon("icon-font"))
admin_sitemap.new(
    modes.view_modes,
    label="Modes",
    svgicon=svgicon.SVGIcon("icon-bars2"))
admin_sitemap.new(
    formats.view_formats,
    label="Transmission formats",
    svgicon=svgicon.SVGIcon("icon-tree"))

moderator_sitemap.label = "Moderator activities"
moderator_sitemap.new(
    events.review,
    label="Review queue",
    svgicon=svgicon.SVGIcon("icon-eye"))

from . import initializer
initializer.create_base_data(Session())
