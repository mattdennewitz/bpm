from __future__ import unicode_literals
import os

from flask import Flask

from .db import Database


app = Flask(__name__)
app.config['database_name'] = os.environ['DATABASE_NAME']

db = Database(app)

from .views import *
