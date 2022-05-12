# -*- coding: UTF-8 -*-

"""
error_handler.py

This view manages the routes
to control redirects after
HTTP error (eg. 404, 500).

last updated : 12/05/2022
"""

from flask import render_template
from app.config import app


@app.errorhandler(404)
def error_404(error):
    """Redirect to 404.html"""
    return render_template('error/404.html', desc=error), 404


@app.errorhandler(500)
def error_500(error):
    """Redirect to 500.html"""
    return render_template('error/500.html', desc=error), 500
