from sqlalchemy import func
import sqlalchemy.exc

import teapot.forms
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
        "edit_alphabet": edit_alphabet,
        "delete_alphabet": delete_alphabet,
        "form": AlphabetForm()
    }, {}

@require_capability("admin")
@router.route("/alphabet/{alphabet_id:d}/edit",
              order=0,
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("alphabet_form.xml")
def edit_alphabet(request: teapot.request.Request, alphabet_id=0):
    form = AlphabetForm()
    existing = request.dbsession.query(
        priyom.model.Alphabet
    ).get(alphabet_id)
    if existing is not None:
        form.short_name = existing.short_name
        form.display_name = existing.display_name


    yield teapot.response.Response(None)
    yield {
        "alphabet_id": alphabet_id,
        "form": form
    }, {}

@require_capability("admin")
@router.route("/alphabet/{alphabet_id:d}/edit",
              order=0,
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("alphabet_form.xml")
def edit_alphabet_POST(request: teapot.request.Request, alphabet_id=0):
    form = AlphabetForm(request=request)

    if not form.errors:
        dbsession = request.dbsession
        existing = dbsession.query(
            priyom.model.Alphabet
        ).get(alphabet_id)
        try:
            if existing is None:
                existing = priyom.model.Alphabet(
                    form.short_name,
                    form.display_name)
            else:
                existing.short_name = form.short_name
                existing.display_name = form.display_name
            dbsession.add(existing)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError:
            teapot.forms.ValidationError(
                "Short name and display name must be unique",
                None,
                form).register()
            dbsession.rollback()
        else:
            raise teapot.make_redirect_response(
                request,
                view_alphabets)

    yield teapot.response.Response(None)

    yield {
        "alphabet_id": alphabet_id,
        "form": form
    }, {}


@require_capability("admin")
@router.route("/alphabet/{alphabet_id:d}/delete",
              order=0,
              methods={teapot.request.Method.GET})
@xsltea_site.with_template("alphabet_delete.xml")
def delete_alphabet(request: teapot.request.Request,
                    alphabet_id=0):
    form = teapot.forms.Form()

    yield teapot.response.Response(None)
    yield {
        "form": form,
        "alphabet_id": alphabet_id
    }, {}

@require_capability("admin")
@router.route("/alphabet/{alphabet_id:d}/delete",
              order=0,
              methods={teapot.request.Method.POST})
@xsltea_site.with_template("alphabet_delete.xml")
def delete_alphabet_POST(request: teapot.request.Request,
                         alphabet_id=0):
    form = teapot.forms.Form()

    dbsession = request.dbsession
    existing = dbsession.query(
        priyom.model.Alphabet
    ).get(alphabet_id)
    if existing is not None:
        try:
            dbsession.delete(existing)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError:
            dbsession.rollback()
            teapot.forms.ValidationError(
                "This alphabet is still in use",
                None,
                form).register()
        else:
            raise teapot.response.make_redirect_response(
                request,
                view_alphabets)

    else:
        teapot.forms.ValidationError(
            "This alphabet does not exist",
            None,
            form).register()

    yield teapot.response.Response(None)
    yield {
        "form": form,
        "alphabet_id": alphabet_id
    }, {}
