import teapot.request

import priyom.model

from .auth import *
from .shared import *
from .pagination import *

class AlphabetForm(teapot.forms.Form):
    @teapot.forms.field
    def short_name(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return value

    @teapot.forms.field
    def display_name(self, value):
        if not value:
            raise ValueError("Must not be empty")
        return value

@require_capability("admin")
@paginate(priyom.model.Alphabet,
          25,
          ("display_name", "asc"),
          "page")
@router.route("/alphabet", order=0, methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_alphabets.xml")
def view_alphabets(request: teapot.request.Request, page):
    alphabets = list(page)

    yield teapot.response.Response(None)

    yield {
        "alphabets": alphabets,
        "page": page,
        "view_alphabets": view_alphabets,
        "form": AlphabetForm()
    }, {}

@require_capability("admin")
@paginate(priyom.model.Alphabet,
          25,
          ("display_name", "asc"),
          "page")
@router.route("/alphabet", order=0, methods={teapot.request.Method.POST})
@xsltea_site.with_template("view_alphabets.xml")
def view_alphabets_POST(request: teapot.request.Request, page):
    form = AlphabetForm(request=request)
    if not form.errors:
        dbsession = request.dbsession
        new_alphabet = priyom.model.Alphabet(
            form.short_name,
            form.display_name)
        dbsession.add(new_alphabet)
        dbsession.commit()
        raise teapot.make_redirect_response(
            request,
            view_alphabets,
            page=page)

    alphabets = list(page)
    yield teapot.response.Response(None)

    yield {
        "alphabets": alphabets,
        "page": page,
        "view_alphabets": view_alphabets,
        "form": form
    }, {}
