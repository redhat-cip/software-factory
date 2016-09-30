# -*- coding: utf-8 -*-
"""
    lodgeit.urls
    ~~~~~~~~~~~~

    The URL mapping.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD
"""
from werkzeug.routing import Map, Rule

urlmap = Map([
    # paste interface
    Rule('/paste/', endpoint='pastes/new_paste'),
    Rule('/paste/+<language>', endpoint='pastes/new_paste'),
    Rule('/paste/show/<identifier>/', endpoint='pastes/show_paste'),
    Rule('/paste/raw/<identifier>/', endpoint='pastes/raw_paste'),
    Rule('/paste/compare/', endpoint='pastes/compare_paste'),
    Rule('/paste/compare/<new_id>/<old_id>/', endpoint='pastes/compare_paste'),
    Rule('/paste/unidiff/<new_id>/<old_id>/', endpoint='pastes/unidiff_paste'),
    Rule('/paste/tree/<identifier>/', endpoint='pastes/show_tree'),

    # captcha for new paste
    Rule('/paste/_captcha.png', endpoint='pastes/show_captcha'),

    # xmlrpc and json
    Rule('/paste/xmlrpc/', endpoint='xmlrpc/handle_request'),
    Rule('/paste/json/', endpoint='json/handle_request'),

    # static pages
    Rule('/paste/about/', endpoint='static/about'),
    Rule('/paste/help/', endpoint='static/help'),
    Rule('/paste/help/<topic>/', endpoint='static/help'),

    # colorscheme
    Rule('/paste/colorscheme/', endpoint='pastes/set_colorscheme'),

    # language
    Rule('/paste/language/<lang>/', endpoint='pastes/set_language'),
])
