from sqlalchemy import func

import teapot.request

import priyom.model

from .auth import *
from .dbview import *
from .shared import *

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
@dbview(priyom.model.Alphabet,
        [
            ("id", priyom.model.Alphabet.id, None),
            ("short_name", priyom.model.Alphabet.short_name, None),
            ("display_name", priyom.model.Alphabet.display_name, None),
            ("user_count", subquery(
                priyom.model.TransmissionContents,
                func.count('*').label('user_count')
            ).group_by(
                priyom.model.TransmissionContents.alphabet_id), int)
        ],
        itemsperpage=25,
        default_orderfield="display_name")
@router.route("/alphabet", order=0, methods={teapot.request.Method.GET})
@xsltea_site.with_template("view_alphabets.xml")
def view_alphabets(request: teapot.request.Request, view):
    alphabets = list(view)

    yield teapot.response.Response(None)

    yield {
        "alphabets": alphabets,
        "view": view,
        "view_alphabets": view_alphabets,
        "form": AlphabetForm()
    }, {}

@require_capability("admin")
@dbview(priyom.model.Alphabet,
        [
            ("id", priyom.model.Alphabet.id, None),
            ("short_name", priyom.model.Alphabet.short_name, None),
            ("display_name", priyom.model.Alphabet.display_name, None),
            ("user_count", subquery(
                priyom.model.TransmissionContents,
                func.count('*').label('user_count')
            ).group_by(
                priyom.model.TransmissionContents.alphabet_id), int)
        ],
        itemsperpage=25,
        default_orderfield="display_name")
@router.route("/alphabet", order=0, methods={teapot.request.Method.POST})
@xsltea_site.with_template("view_alphabets.xml")
def view_alphabets_POST(request: teapot.request.Request, view):
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
            view=view)

    alphabets = list(page)
    yield teapot.response.Response(None)

    yield {
        "alphabets": alphabets,
        "page": page,
        "view_alphabets": view_alphabets,
        "form": form
    }, {}
