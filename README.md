# **youtube-wpm**


## Summary

`youtube-wpm` is a CLI tool to get a YouTube video's words per minute (WPM).

[![PyPI version](https://badge.fury.io/py/youtube-wpm.svg)](https://badge.fury.io/py/youtube-wpm)
![Python Version](https://img.shields.io/pypi/pyversions/youtube-wpm)
[![CI](https://github.com/thombashi/youtube-wpm/actions/workflows/ci.yml/badge.svg)](https://github.com/thombashi/youtube-wpm/actions/workflows/ci.yml)
[![CodeQL](https://github.com/thombashi/youtube-wpm/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/thombashi/youtube-wpm/actions/workflows/github-code-scanning/codeql)


## Installation

```
pip install youtube-wpm
```


## Usage

```
$ youtube-wpm https://youtu.be/QpBTM0GO6xI
- Title: [Google I/O '23 in under 10 minutes](http://youtube.com/watch?v=QpBTM0GO6xI)
- Channel: [Google](https://www.youtube.com/channel/UCK8sQmJBp8GCxrOtXWBpyEA)
- Time: 9m 39s
- WPM: 179.3
- Auto Gen Transcript: False
```

Fetch multiple YouTube videos' information as a Markdown table:

```
$ youtube-wpm --format=md-table QpBTM0GO6xI qSkB8-zL3Mo
```

Output:

|                                    Title                                     |                              Channel                               |  Time  |  WPM  | Auto Gen Transcript |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------ | ----: | ------------------- |
| [Google I/O '23 in under 10 minutes](http://youtube.com/watch?v=QpBTM0GO6xI) | [Google](https://www.youtube.com/channel/UCK8sQmJBp8GCxrOtXWBpyEA) | 9m 39s | 179.3 | False               |
| [Google Cloud \| Google I/O 2023](http://youtube.com/watch?v=qSkB8-zL3Mo)     | [Google](https://www.youtube.com/channel/UCK8sQmJBp8GCxrOtXWBpyEA) | 9m 27s | 169.4 | False               |


## Command help

```
usage: youtube-wpm [-h] [-V] [-v] [--language LANGUAGE] [--initial-wpm INITIAL_WPM] [--format {markdown,md-table}] [--length-format {short,long}] [--debug | --quiet] VIDEO_ID [VIDEO_ID ...]

A CLI tool to get a YouTube video's words per minute (WPM).

positional arguments:
  VIDEO_ID              YouTube video IDs

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose
  --language LANGUAGE   language code of the transcript (default: en)
  --initial-wpm INITIAL_WPM
                        initial approximate words per minute (default: 180)
  --debug               for debug print (default: LogLevel.INFO)
  --quiet               suppress execution log messages (default: LogLevel.INFO)

Output Format:
  --format {markdown,md-table}
                        output format (default: markdown)
  --length-format {short,long}
                        output format of the video length (default: short)

Issue tracker: https://github.com/thombashi/youtube-wpm/issues
```


## Dependencies
- Python 3.8+
