from __future__ import unicode_literals
import logging

from peewee import Model
from playhouse.postgres_ext import PostgresqlExtDatabase


logger = logging.getLogger('peewee')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class Database(object):
    def __init__(self, app):
        self.app = app
        self.create_database()
        self.register_connection_handlers()

        self.Model = self.get_model_class()

    def create_database(self):
        self.database = PostgresqlExtDatabase(self.app.config['database_name'])

    def get_model_class(self):
        class BaseModel(Model):
            class Meta:
                database = self.database
        return BaseModel

    def _db_connect(self):
        self.database.connect()

    def _db_disconnect(self, exc):
        if not self.database.is_closed():
            self.database.close()

    def register_connection_handlers(self):
        self.app.before_request(self._db_connect)
        self.app.teardown_request(self._db_disconnect)
