# **youtube-wpm**


## Summary

`youtube-wpm` is a CLI tool to get a YouTube video's words per minute (WPM).


## Installation

```
pip install youtube-wpm
```


## Usage

```
$ youtube-wpm https://youtu.be/QpBTM0GO6xI
Total word count: 1373
Approximate blank time: 1 minutes 47 seconds
Approximate speaking time: 7 minutes 39 seconds
Words Per Minute: 179.1
```


## Command help

```
usage: youtube-wpm [-h] [-V] [--language LANGUAGE] [--initial-wpm INITIAL_WPM] [--debug | --quiet] video_id

A CLI tool to calculate the words per minute (WPM) of a YouTube video.

positional arguments:
  video_id              Youtube video ID

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  --language LANGUAGE   language code of the transcript. defaults to 'en'.
  --initial-wpm INITIAL_WPM
                        initial approximate words per minute. defaults to 180.
  --debug               for debug print.
  --quiet               suppress execution log messages.

Issue tracker: https://github.com/thombashi/youtube-wpm/issues
```


## Dependencies
- Python 3.8+
