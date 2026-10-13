# This file contains the routes for search related tasks
from flask import request, render_template, Blueprint
import ytdlphandler

# Define search blueprint
search = Blueprint('search', __name__)

# Results route with query
@search.route('/results')
def results():
    # Get search query
    query = request.args.get("q")

    # If no query is specified, show empty results page
    if not query:
        return render_template('searchPage.html', title = "Search", videos = [])

    # Get search results
    searchResults = ytdlphandler.search(query)
    return render_template('searchPage.html', title = query, videos = searchResults)

# Results route for related
@search.route('/related')
def related():
    # Get video ID
    videoID = request.args.get("v")

    # Get related videos
    relatedVideos = ytdlphandler.related(videoID)

    return render_template('searchPage.html', title = "Related Videos", videos = relatedVideos)
