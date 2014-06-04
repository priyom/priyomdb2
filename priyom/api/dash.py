import teapot
import teapot.request

import priyom.model

from .auth import *
from .shared import *

@router.route("/", methods={teapot.request.Method.GET})
@xsltea_site.with_variable_template()
def dash(request: teapot.request.Request):
    if request.auth.user:
        yield "dash-authed.xml"
    else:
        yield "dash-unauthed.xml"

    dbsession = request.dbsession
    yield teapot.response.Response(None)

    transform_args = {
        "version": "devel"
    }
    template_args = dict(transform_args)

    template_args["recents"] = dbsession.query(
        priyom.model.Event
    ).order_by(
        priyom.model.Event.created.desc()
    ).limit(10)

    if request.auth.has_capability(Capability.REVIEW_LOG):
        template_args["unapproved"] = dbsession.query(
            priyom.model.Event
        ).filter(
            priyom.model.Event.approved == False
        ).order_by(
            priyom.model.Event.created.asc()
        ).limit(10)
    else:
        template_args["unapproved"] = None

    if request.auth.user:
        template_args["mine"] = dbsession.query(
            priyom.model.Event
        ).filter(
            priyom.model.Event.submitter_id == request.auth.user.id
        ).order_by(
            priyom.model.Event.created.desc()
        ).limit(10)
    else:
        template_args["mine"] = None
        from . import login
        template_args["signup_form"] = login.SignupForm()
        template_args["signup"] = login.signup

    from . import log, login, stations, events

    template_args.update({
        "log_tx": log.log,
        "sign_in": login.login,
        "view_station": stations.get_station_viewer(request),
        "view_event": events.get_event_viewer(request),
    })

    yield (template_args, transform_args)
