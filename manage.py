#!/usr/bin/env python

from __future__ import unicode_literals

import click

from www import db
from www.models import Artist, Release, Genre, Track


@click.group()
def cli(): pass


@cli.command()
def create_tables():
    db._db_connect()

    for Model in (Artist, Release, Genre, Track):
        db.database.create_table(Model)


if __name__ == '__main__':
    cli()

