#!/usr/bin/env python

"""Retrieves ID3, calculates bpm and Chromaprint from
recursively discovered files.
"""

from __future__ import unicode_literals
import json
import logging
import multiprocessing
from multiprocessing.dummy import Pool
import os
import subprocess
import sys
import time

import click

import psycopg2


find_mp3s = lambda f: f.endswith('.mp3')

scan_for_fingerprint = lambda l: l.startswith('FINGERPRINT=')


# configure logger
log = logging.getLogger('get-bpm')
out_h = logging.FileHandler('progress.log', 'a')
fmt = logging.Formatter('%(asctime)s [%(name)s/%(funcName)s] %(message)s')
out_h.setFormatter(fmt)
log.addHandler(out_h)
log.setLevel(logging.INFO)


def get_bpm(path):
    "Decodes file with `sox`, processes with `bpm`, returns bpm value"

    cmd = 'sox -V1 "' + path + '" -r 44100 -e float -c 1 -t raw - | bpm'

    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        log.error('<%s> BPM extraction failed: %s' % (path, err))
        return None

    return float(out.strip())


def analyze_and_echoprint(path):
    """Runs `echoprint-codegen` to

    - fingerprint
    - extract ID3
    - extract bitrate and duration
    """

    proc = subprocess.Popen(['echoprint-codegen', path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        log.error('<%s> Could not fingerprint: %s' % (path, err))
        return None

    try:
        return json.loads(out.strip())[0]
    except IndexError:
        log.error('<%s> Could not extract fingerprint: %s' % (path, exc))
        return None

def get_chromaprint(path):
    "Uses `fpcalc` to calculate a fingerprint"

    proc = subprocess.Popen(['fpcalc', path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        log.error('<%s> Could not extract fingerprint: %s' % (path, err))
        return None

    # extract fingerprint from output
    try:
        fp_lines = filter(scan_for_fingerprint, out.split())
        return fp_lines[0].strip().replace('FINGERPRINT=', '')
    except (IndexError, UnicodeDecodeError) as exc:
        log.error('<%s> Could not extract fingerprint: %s' % (path, exc))
        return None


def gather_info(path):
    "Scans for artist, title, and BPM"

    log.info('<%s> Analyzing' % path)

    try:
        szof = os.path.getsize(path)
    except os.error:
        log.error('<%s> Path not a file' % path)
        return False

    # nothing larger than 50mb,
    # which should cover everything under 15-20 minutes
    if szof > 50000000:
        log.error('<%s> Skipping too large a file: %s' % (path, szof))
        return False

    # run most-in-one scan with `echoprint-codegen`,
    # which will return audio metadata *and* fingerprint
    audio_info_and_echoprint = analyze_and_echoprint(path)

    if not audio_info_and_echoprint:
        # todo: implement fallbacks
        return None

    meta = audio_info_and_echoprint.get('metadata', {})

    if 'duration' in meta:
        if meta['duration'] > 30 * 60:
            # todo: log that we bailed over duration > 30 minutes
            log.error('<%s> Skipping too long a track: %s' % (
                path, meta['duration']))
            return None

    artist = meta.get('artist')
    title = meta.get('title')

    if not artist and title:
        log.error('<%s> Skipping improperly tagged file' % path)
        return None

    # construct id3
    id3_blob = {
        'artist': artist,
        'title': title,
        'genre': meta.get('genre'),
        'release': meta.get('release'),
    }

    # chromaprint, just for posterity
    chromaprint = get_chromaprint(path)

    log.info('<%s> Analysis complete. Saving.' % path)

    conn = psycopg2.connect('dbname=bpm_data')
    cursor = conn.cursor()

    # ensure what we're about to insert
    # does not alread exist
    cursor.execute('select 1 from scanned where fn = %s', (path, ))
                   # (audio_info_and_echoprint['code'], ))
    res = cursor.fetchall()

    if res:
        log.warning('<%s> Skipping existing track (from print)' % path)
        return None

    # measure bpm
    bpm = get_bpm(path)

    values = {
        'bpm': bpm,
        'duration': meta['duration'],
        'bitrate': meta['bitrate'],
        'id3': json.dumps(id3_blob),
        'chromaprint': chromaprint,
        'echoprint': audio_info_and_echoprint['code'],
        'fn': path,
    }

    cursor.execute("""
insert into
    scanned (
      bpm, duration, bitrate, id3, chromaprint, echoprint, fn
    )
values
    (
      %(bpm)s, %(duration)s, %(bitrate)s, %(id3)s
      , %(chromaprint)s, %(echoprint)s, %(fn)s
    )
;
    """, values)

    conn.commit()

    return True


@click.command()
@click.option('-p', '--path', help='Path to scan for .mp3s')
@click.option('-w', '--workers', default=multiprocessing.cpu_count,
              help='Path to scan for .mp3s')
@click.option('-s', '--solo', is_flag=True)
def scan(path, workers, solo):
    path = os.path.realpath(path)
    start = time.time()
    c = 0

    if not solo:
        pool = Pool(workers)

    for root, sub_fs, files in os.walk(path):
        mp3s = filter(find_mp3s, files)

        for mp3 in mp3s:
            mp3_path = os.path.join(root, mp3)

            c += 1

            if not solo:
                pool.imap(gather_info, (mp3_path, ))
            else:
                gather_info(mp3_path)

    if not solo:
        pool.close()
        pool.join()

    print (time.time() - start) / 60

    print c


if __name__ == '__main__':
    scan()


# def get_mutagen_audio_info(path):
#     "Uses `mutagen` to read an audio file's duration"
#
#     audio = MP3(path)
#
#     return (audio.info.length, audio.info.bitrate)


# def get_id3(path):
#     "Uses `mutagen` lib to grab artist, album, and title information"
#
#     try:
#         return ID3(path)
#     except Exception as exc:
#         # todo: log exception
#         return {}
