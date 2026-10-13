# This file contains the routes for featured page related tasks
from flask import render_template, Blueprint
import ytdlphandler

# Define homepage blueprint
featured = Blueprint('featured', __name__)

# featuredPage route
@featured.route('/featuredPage')
def featuredPage():
    return render_template('featured.html', title = "Featured", videos = ytdlphandler.trending())
