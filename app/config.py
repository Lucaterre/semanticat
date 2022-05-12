# -*- coding: UTF-8 -*-

"""
config.py

Groups Flask environment constants and variables/
global configuration when creating the Semantic@ app according
to the selected mode (prod, dev, test)

last updated : 12/05/2022
"""


import os
import logging

import colorlog

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

LOGGER = logging.getLogger('[SEMANTIC@]')

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter())
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

PATH = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {"xml", "txt"}
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
    """Configuration used in production mode."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + PRODUCTION_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENV = "production"


class DevConfig(BaseConfig):
    """Configuration used in development mode."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + DEV_DB
    FLASK_ENV = "development"


class TestConfig(BaseConfig):
    """Configuration used in test mode."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////" + TEST_DB
    FLASK_ENV = "testing"


def create_app(config=None, erase_recreate=False):
    """Create and configure the app with correct
    configuration mode."""
    if config is None:
        LOGGER.info('Start Semantic@...')
        app.config.from_object(BaseConfig)
    elif config == "dev":
        LOGGER.info('Initialize Semantic@ dev mode...')
        app.config.from_object(DevConfig)
    elif config == "test":
        LOGGER.info('Initialize Semantic@ test mode...')
        app.config.from_object(TestConfig)
    db.init_app(app)
    with app.app_context():
        if erase_recreate:
            LOGGER.critical('Erase all database...')
            db.drop_all()
        LOGGER.warning('Create all database...')
        db.create_all()
        return app
