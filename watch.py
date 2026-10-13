# This file contains the routes for video related tasks
import glob
from flask import request, render_template, redirect, url_for, Blueprint, Response
import ytdlphandler
import urllib.request
import subprocess
import os
import os.path
import config

# Define watch blueprint
watch = Blueprint('watch', __name__)

VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'videos')

# Get folder size
def getFolderSize(folder):
    total = 0
    for entry in os.scandir(folder):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += getFolderSize(entry.path)
    return total

def remove_partial(path):
    for candidate in (path, path + '.part', path + '.ytdl'):
        if os.path.exists(candidate):
            try:
                os.remove(candidate)
            except OSError:
                pass

# Video page route
@watch.route('/watch')
def video():
    # Get video ID
    videoID = request.args.get("v")
    if not ytdlphandler.valid_video_id(videoID):
        return "Invalid video."

    cachedName = 'videos/' + videoID + '-mp4v.mp4'
    cachedPath = os.path.join(VIDEO_DIR, videoID + '-mp4v.mp4')

    # Check if the video is already on the server in the videos folder. If so, redirect to cached file
    if os.path.exists(cachedPath):
        return redirect(url_for('static', filename=cachedName))

    seconds, error = ytdlphandler.video_duration(videoID)
    if error:
        return error

    # If the video is longer than maximum length in config, return an alert error
    if seconds is None or seconds > config.MAXIMUM_LENGTH:
        return "Videos longer than " + str(config.MAXIMUM_LENGTH) + " seconds are not supported."

    os.makedirs(VIDEO_DIR, exist_ok=True)

    # While cached folder size is greater than 10GB, delete oldest file if it is not in use
    while getFolderSize(VIDEO_DIR) > config.CACHE_SIZE:
        cachedFiles = list(glob.iglob(os.path.join(VIDEO_DIR, '*')))
        if not cachedFiles:
            break

        # Get oldest file
        oldestFile = min(cachedFiles, key=os.path.getctime)

        # Try to delete oldest file. If the process fails 5 times, stop the process
        removed = False
        for i in range(5):
            try:
                os.remove(oldestFile)
                removed = True
                break
            except:
                pass
        if not removed:
            break

    sourcePath = os.path.join(VIDEO_DIR, videoID + '.mp4')
    downloadError = ytdlphandler.download(videoID, sourcePath)
    if downloadError:
        remove_partial(sourcePath)
        return downloadError

    # Convert downloaded video to 24 fps mp4v encoding using ffmpeg
    transcode = subprocess.call(['ffmpeg', '-y', '-i', sourcePath, '-r', '24', '-c:v', 'mpeg4', '-preset', 'fast', '-crf', '5', '-c:a', 'copy', cachedPath])

    # Delete the original video
    remove_partial(sourcePath)

    if transcode != 0 or not os.path.exists(cachedPath):
        if os.path.exists(cachedPath):
            try:
                os.remove(cachedPath)
            except OSError:
                pass
        return "Could not prepare this video."

    # Redirect user to downloaded video
    return redirect(url_for('static', filename=cachedName))

# Add route for thumbnail
@watch.route('/thumbnail')
def thumbnail():
    # Get video ID
    videoID = request.args.get("v")
    if not ytdlphandler.valid_video_id(videoID):
        return "Invalid video."

    imageRequest = urllib.request.Request(
        'https://i.ytimg.com/vi/' + videoID + '/mqdefault.jpg',
        headers={'User-Agent': 'Mozilla/5.0'},
    )
    try:
        with urllib.request.urlopen(imageRequest, timeout=30) as imageResponse:
            image = imageResponse.read()
    except Exception:
        return "Could not load thumbnail."

    # Return thumbnail image
    return Response(image, mimetype='image/jpeg')

# Video info page route
@watch.route('/videoinfo')
def videoinfo():
    # Get video ID
    videoID = request.args.get("v")
    if not ytdlphandler.valid_video_id(videoID):
        return "Invalid video."

    title = ytdlphandler.video_title(videoID)
    if not title:
        return "Could not load this video."

    video = {'videoId': videoID, 'title': title}
    return render_template('videoPage.html', title = title, video = video)
