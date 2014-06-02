import teapot
import teapot.request

import priyom.model

from .auth import *
from .shared import *

from .log import log

@require_login()
@router.route("/", methods={teapot.request.Method.GET})
@xsltea_site.with_template("dash.xml")
def dash(request: teapot.request.Request):
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
    template_args["mine"] = dbsession.query(
        priyom.model.Event
    ).filter(
        priyom.model.Event.submitter_id == request.auth.user.id
    ).order_by(
        priyom.model.Event.created.desc()
    ).limit(10)

    template_args.update({
        "log_tx": log,
    })

    yield (template_args, transform_args)

@require_login()
@router.route("/logout", methods={teapot.request.Method.GET})
def logout(request: teapot.request.Request):
    from .anonymous_user import anonhome
    response = teapot.make_redirect_response(request, anonhome)
    response.cookies["api_session_key"] = ""
    response.cookies["api_session_key"]["Expires"] = 1
    return response
