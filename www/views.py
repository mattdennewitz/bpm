from flask import render_template

from www import app
from www.models import Track


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/track/<slug>/')
def track_detail(slug):
    return 'track'

