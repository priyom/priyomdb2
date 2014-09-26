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
    priyom.config.get_data_path("css"),
    "f",
    filterfunc=lambda x: x.endswith(".css"))
@router.route(methods={teapot.request.Method.GET})
def css_file(f):
    return teapot.response.Response.file(
        teapot.mime.Type("text", "css").with_charset("utf-8"),
        f)


@teapot.file_from_directory(
    "/img/",
    priyom.config.get_data_path("img"),
    "f")
@router.route(methods={teapot.request.Method.GET})
def img_file(f):
    _, ext = os.path.splitext(f.name)

    mimetype = mimetypes.get(ext, mimetypes[None])

    return teapot.response.Response.file(mimetype, f)

def logged_in(node, request):
    return request.auth and request.auth.user

def logged_out(node, request):
    return not request.auth or not request.auth.user

# Sitemap: Common activities
user_sitemap.new(
    dash.dash,
    label="Dash",
    svgicon=svgicon.SVGIcon("icon-bars"))

group1 = user_sitemap.new(
    stations.view_stations,
    label="Stations",
    svgicon=svgicon.SVGIcon("icon-podcast"),
    children_visible_predicate=False)
group1.new(
    stations.view_station,
    label="View station")
group1.new(
    stations.edit_station,
    label="Edit station")

group1 = user_sitemap.new(
    events.view_events,
    label="Events",
    svgicon=svgicon.SVGIcon("icon-info-circle"),
    children_visible_predicate=False)
group1.new(
    events.edit_event,
    label="Edit event",
    aliased_routables={events.edit_event_POST})

user_sitemap.new(
    log.log,
    label="Log TX",
    svgicon=svgicon.SVGIcon("icon-microphone"),
    aliased_routables={log.log_POST},
    visible_predicate=logged_in)
user_sitemap.new(
    users.edit_self,
    label="My account",
    svgicon=svgicon.SVGIcon("icon-user"),
    aliased_routables={users.edit_self_POST},
    visible_predicate=logged_in)
user_sitemap.new(
    login.logout,
    label="Sign out",
    svgicon=svgicon.SVGIcon("icon-exit"),
    visible_predicate=logged_in)
user_sitemap.new(
    login.login,
    label="Sign in",
    svgicon=svgicon.SVGIcon("icon-enter"),
    visible_predicate=logged_out)

# Sitemap: Moderator activities
moderator_sitemap.new(
    events.review,
    label="Review queue",
    svgicon=svgicon.SVGIcon("icon-eye"))

# Sitemap: Admin activities
group1 = admin_sitemap.new(
    alphabets.view_alphabets,
    label="Alphabets",
    svgicon=svgicon.SVGIcon("icon-font"),
    children_visible_predicate=False)
group1.new(
    alphabets.edit_alphabet,
    label="Edit alphabet",
    aliased_routables={alphabets.edit_alphabet_POST})

group1 = admin_sitemap.new(
    modes.view_modes,
    label="Modes",
    svgicon=svgicon.SVGIcon("icon-bars2"),
    children_visible_predicate=False)
group1.new(
    modes.edit_mode,
    label="Edit mode",
    aliased_routables={modes.edit_mode_POST})

group1 = admin_sitemap.new(
    formats.view_formats,
    label="Transmission formats",
    svgicon=svgicon.SVGIcon("icon-tree"),
    children_visible_predicate=False)
group1.new(
    formats.edit_format,
    label="Edit format",
    aliased_routables={formats.edit_format_POST})
