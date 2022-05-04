#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse

import pyfiglet

from app.config import create_app


def semanticat_cli():
    SEMANTICAT_LOGO = pyfiglet.figlet_format("SEMANTIC@")
    print(SEMANTICAT_LOGO)
    print("XML formats with semantic annotations © 2022\n")

    parser = argparse.ArgumentParser()
    parser.add_argument('--dev_mode', action='store_true')
    parser.add_argument('--erase_recreate_db', action='store_true')
    args = parser.parse_args()

    PORT = 3000
    dropDB = False

    if args.erase_recreate_db:
        dropDB = True

    if args.dev_mode:
        app = create_app(config="dev",
                         erase_recreate=dropDB)
        app.run(port=PORT)
    else:
        app = create_app(config=None,
                         erase_recreate=dropDB)
        app.run(port=PORT)


if __name__ == '__main__':
    semanticat_cli()
