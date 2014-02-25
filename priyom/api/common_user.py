import teapot
import teapot.request

from .shared import *
from .auth import *

@require_login()
@router.route("/", methods={teapot.request.Method.GET}, order=0)
@xsltea_site.with_template("dash.xml")
def dash(request: teapot.request.Request):
    yield teapot.response.Response(None)
    transform_args = {
        "version": "devel"
    }
    template_args = dict(transform_args)
    template_args["auth"] = request.auth
    yield (template_args, transform_args)

@require_login()
@router.route("/logout", methods={teapot.request.Method.GET})
def logout(request: teapot.request.Request):
    from .anonymous_user import anonhome
    response = teapot.make_redirect_response(request, anonhome)
    response.cookies["api_session_key"] = ""
    response.cookies["api_session_key"]["Expires"] = 1
    return response
