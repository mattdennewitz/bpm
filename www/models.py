from __future__ import unicode_literals

from peewee import (CharField, IntegerField, FloatField,
                    ForeignKeyField, Model, TextField)
from playhouse.postgres_ext import ArrayField, JSONField

from www import db
from www.fields import SlugField

import logging
l = logging.getLogger('peewee')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())


class ScannedTrack(db.Model):
    "Container for a track scanned by our hodge-podge toolset"

    bpm = FloatField()
    duration = FloatField()
    bitrate = IntegerField()
    id3 = JSONField()
    fn = CharField()

    # fingerprints
    chromaprint = TextField()
    echoprint = TextField()


#
# entities
#

class Entity(db.Model):
    name = CharField()
    slug = SlugField(populate_from='name', unique=True)
    mbids = ArrayField(CharField)


class Artist(Entity):
    pass


class Genre(Entity):
    pass


class Release(Entity):
    year = IntegerField()


class Track(Entity):
    "A single track, which has already been scanned"
    title = CharField()
    bpm = FloatField()


class ReleaseArtist(db.Model):
    release = ForeignKeyField(Release)
    artist = ForeignKeyField(Artist)


class ReleaseTrack(db.Model):
    release = ForeignKeyField(Release)
    track = ForeignKeyField(Track)
