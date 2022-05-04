# -*- coding: UTF-8 -*-

from flask import (redirect,
                   url_for,
                   request)

from app.config import (app,
                        db,
                        LOGGER)


@app.route('/recreate_db')
def clean_db():
    """Destroy and recreate all database from front"""
    LOGGER.critical('Clean all database...')
    db.drop_all()
    LOGGER.warning('Recreate all database...')
    db.create_all()
    return redirect(url_for('index'))


@app.get('/shutdown')
def shutdown():
    """Shutdown the server"""
    LOGGER.info('Goodbye !')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return '<h1>Semantic@ stop and server shutting down...</h1>'
