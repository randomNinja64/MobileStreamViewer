# MobileStreamViewer

## Description

A web based frontend for [yt-dlp](https://github.com/yt-dlp/yt-dlp) for iPhone OS 1.0 and up.

## Configuration (`config.py`)

* **Secret Key** - Flask secret key (default: `MobileVideoShare`)
* **Cache Size** - Maximum size of the video cache, in bytes. Oldest cached files are removed when the cache grows past this size (default: `10000000000`)
* **Maximum Length** - Longest video that can be watched, in seconds (default: `1800`)

## Installation

Install the packages in `requirements.txt`. For testing, run main.py. For production, deploy via a WSGI server.

The application depends on FFMPEG. Please either place a directory containing ffmpeg.exe in your Path environment variable or place a copy of ffmpeg.exe in the folder with this application

## Usage

To view a video, locate one using video search or the Trending page. To view related videos after viewing a video, use the Related Videos option.

## Licensing

InvidiousMobile is licensed under the MIT license.
