from __future__ import unicode_literals

from peewee import (CharField, IntegerField, FloatField,
                    ForeignKeyField, TextField)
from playhouse.postgres_ext import JSONField

from www import db
from www.fields import SlugField


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

    class Meta:
        db = db.database
        db_table = 'scanned'


class Artist(db.Model):
    name = CharField()
    slug = SlugField(unique=True)


class Genre(db.Model):
    name = CharField()
    slug = SlugField(unique=True)


class Release(db.Model):
    artist = ForeignKeyField(Artist, related_name='releases')
    name = CharField()
    slug = SlugField(unique=True)


class Track(db.Model):
    "A single track, which has already been scanned"

    artist = ForeignKeyField(Artist, related_name='tracks', null=True)
    release = ForeignKeyField(Release, related_name='tracks', null=True)
    genre = ForeignKeyField(Genre, related_name='tracks', null=True)
    title = CharField()
    bpm = FloatField()

    def get_full_title(self):
        return '%s: %s' % (self.artist.name, self.title)
