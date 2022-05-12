# -*- coding: UTF-8 -*-

import os
import colorlog
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from werkzeug.middleware.profiler import ProfilerMiddleware

LOGGER = logging.getLogger('[SEMANTIC@]')

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter())
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

PATH = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {"xml"}
TEMPLATES = os.path.join(PATH, 'templates')
STATICS = os.path.join(PATH, 'static')

PRODUCTION_DB = os.path.join(PATH, "./db_config/semanticat.db")
DEV_DB = os.path.join(PATH, "./db_config/semanticat_dev.db")
TEST_DB = os.path.join(PATH, "./db_config/semanticat_test.db")

DEBUG = False

app = Flask("Semantic@",
            template_folder=TEMPLATES,
            static_folder=STATICS,
            instance_relative_config=True)

db = SQLAlchemy()


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + PRODUCTION_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = "production"


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + DEV_DB
    FLASK_ENV = "development"


class TestConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + TEST_DB
    FLASK_ENV = "testing"


def create_app(config=None, erase_recreate=False):
    if config is None:
        LOGGER.info('Start Semantic@...')
        app.config.from_object(BaseConfig)
    elif config == "dev":
        LOGGER.info('Initialize Semantic@ dev mode...')
        # app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
        app.config.from_object(DevConfig)
    elif config == "test":
        LOGGER.info('Initialize Semantic@ test mode...')
        app.config.from_object(TestConfig)
    db.init_app(app)
    with app.app_context():
        from . import views
        if erase_recreate:
            LOGGER.critical('Erase all database...')
            db.drop_all()
        LOGGER.warning('Create all database...')
        db.create_all()
        return app
