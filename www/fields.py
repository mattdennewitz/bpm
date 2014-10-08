from __future__ import unicode_literals

import re

import translitcodec

from peewee import CharField


__all__ = ('SlugField', )

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim='-'):
    """Generates an ASCII-only slug.

    Taken from http://flask.pocoo.org/snippets/5/.
    """

    result = []

    for word in _punct_re.split(text.lower()):
        word = word.encode('translit/long')

        if word:
            result.append(word)

    return unicode(delim.join(result))


class SlugField(CharField):
    def coerce(self, value):
        return slugify(value)
