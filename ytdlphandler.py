import json
import os
import re
import subprocess
import sys

RESULT_COUNT = 20
VIDEO_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')

FLAT_FLAGS = [
    '-j',
    '--flat-playlist',
    '--no-warnings',
    '--encoding', 'utf-8',
    '--extractor-args', 'youtubetab:approximate_date',
    '-I', '1:' + str(RESULT_COUNT),
]


def valid_video_id(video_id):
    return bool(video_id and VIDEO_ID_RE.match(video_id))


def run_ytdlp(args):
    command = [sys.executable, '-m', 'yt_dlp'] + args
    run_kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'stdin': subprocess.DEVNULL,
        'check': False,
    }
    if os.name == 'nt':
        run_kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

    try:
        completed = subprocess.run(command, **run_kwargs)
    except OSError as error:
        return 1, '', str(error)

    stdout = completed.stdout.decode('utf-8', 'replace')
    stderr = completed.stderr.decode('utf-8', 'replace')
    return completed.returncode, stdout, stderr


def error_text(stderr, fallback):
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    if not lines:
        return fallback
    text = lines[-1]
    if len(text) > 240:
        text = text[-240:]
    return text


def parse_flat_json(stdout):
    videos = []
    seen = set()
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        video_id = item.get('id') or ''
        title = (item.get('title') or '').strip()
        if not valid_video_id(video_id) or not title or video_id in seen:
            continue

        live_status = item.get('live_status') or ''
        if live_status in ('is_live', 'is_upcoming'):
            continue

        videos.append({'videoId': video_id, 'title': title})
        seen.add(video_id)
    return videos


def list_videos(target):
    stdout = run_ytdlp(FLAT_FLAGS + [target])[1]
    return parse_flat_json(stdout)[:RESULT_COUNT]


def search(query):
    return list_videos('ytsearch' + str(RESULT_COUNT) + ':' + query)


def trending():
    # YouTube removed the general trending page in 2025. Try it first, then the
    # gaming trending feed, which is the trending tab yt-dlp can still extract.
    for url in (
        'https://www.youtube.com/feed/trending',
        'https://www.youtube.com/gaming/trending',
    ):
        videos = list_videos(url)
        if videos:
            return videos
    return []


def video_title(video_id):
    if not valid_video_id(video_id):
        return None

    code, stdout, stderr = run_ytdlp([
        '--flat-playlist',
        '--no-warnings',
        '--encoding', 'utf-8',
        '--no-playlist',
        '--print', '%(title)s',
        'https://www.youtube.com/watch?v=' + video_id,
    ])
    for line in stdout.splitlines():
        title = line.strip()
        if title and title != 'NA':
            return title
    return None


def related(video_id):
    if not valid_video_id(video_id):
        return []

    videos = list_videos('https://www.youtube.com/playlist?list=RD' + video_id)
    videos = [video for video in videos if video['videoId'] != video_id]
    if videos:
        return videos[:RESULT_COUNT]

    title = video_title(video_id)
    if not title:
        return []

    videos = search(title)
    return [video for video in videos if video['videoId'] != video_id][:RESULT_COUNT]


def video_duration(video_id):
    code, stdout, stderr = run_ytdlp([
        '--no-download',
        '--no-warnings',
        '--no-playlist',
        '--encoding', 'utf-8',
        '--print', '%(duration)s',
        'https://www.youtube.com/watch?v=' + video_id,
    ])

    text = ''
    for line in stdout.splitlines():
        if line.strip():
            text = line.strip()
            break

    if text and text != 'NA':
        try:
            return int(float(text)), None
        except ValueError:
            pass

    if code != 0:
        return None, error_text(stderr, 'Could not load this video.')
    return None, None


def download(video_id, dest_path):
    code, stdout, stderr = run_ytdlp([
        '-S', 'res:360,vcodec:h264,acodec:aac,ext:mp4:m4a',
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--no-warnings',
        '--quiet',
        '--force-overwrites',
        '-o', dest_path,
        'https://www.youtube.com/watch?v=' + video_id,
    ])
    if code != 0 or not os.path.exists(dest_path):
        return error_text(stderr, 'Download failed.')
    return None
