import argparse
import sys
from decimal import Decimal
from textwrap import dedent

import humanreadable as hr
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from .__version__ import __version__
from ._const import EXIT_WPM_DIFF_THRESHOLD, INITIAL_APPROXIMATE_WPM, MAX_ITERATION, MODULE_NAME
from ._logger import LogLevel, initialize_logger, logger
from ._youtube import calc_speak_time, normalize_youtube_id


def parse_option() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(
            """\
            A CLI tool to get a YouTube video's words per minute (WPM).
            """
        ),
        epilog=dedent(
            f"""\
            Issue tracker: https://github.com/thombashi/{MODULE_NAME}/issues
            """
        ),
    )
    parser.add_argument("video_id", help="Youtube video ID")

    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    parser.add_argument(
        "--language",
        default="en",
        help="language code of the transcript. defaults to 'en'.",
    )
    parser.add_argument(
        "--initial-wpm",
        type=float,
        default=INITIAL_APPROXIMATE_WPM,
        help=f"initial approximate words per minute. defaults to {INITIAL_APPROXIMATE_WPM}.",
    )

    loglevel_dest = "log_level"
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--debug",
        dest=loglevel_dest,
        action="store_const",
        const=LogLevel.DEBUG,
        default=LogLevel.INFO,
        help="for debug print.",
    )
    group.add_argument(
        "--quiet",
        dest=loglevel_dest,
        action="store_const",
        const=LogLevel.QUIET,
        default=LogLevel.INFO,
        help="suppress execution log messages.",
    )

    return parser.parse_args()


def calc_seconds_per_word(wpm: Decimal) -> Decimal:
    return 60 / wpm


def main() -> int:
    ns = parse_option()

    initialize_logger(name=MODULE_NAME, log_level=ns.log_level)

    video_id = normalize_youtube_id(ns.video_id)
    logger.debug(f"fetching transcripts of {video_id} ...")

    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled as e:
        logger.error(e)
        return 1

    try:
        transcript = transcripts.find_transcript([ns.language])
    except NoTranscriptFound as e:
        logger.error(e)
        return 1

    logger.debug(
        f"{video_id=}, {transcript.language=}, {transcript.language_code=}, {transcript.is_generated=}"
    )

    initial_wpm: Decimal = Decimal(200)
    prev_wpm: Decimal = initial_wpm
    inference_spw = calc_seconds_per_word(prev_wpm)

    sequences = transcript.fetch()
    for i in range(MAX_ITERATION):
        stat = calc_speak_time(sequences, inference_spw=inference_spw)
        diff_wpm = abs(stat.wpm - prev_wpm)
        logger.debug(f"iteration={i}, wpm={stat.wpm:.1f}, diff_wpm={diff_wpm:.1f}")
        if diff_wpm < EXIT_WPM_DIFF_THRESHOLD:
            break

        inference_spw = calc_seconds_per_word(stat.wpm)
        prev_wpm = stat.wpm

    assert stat.total_speak_secs > 0
    outputs = [
        f"Total word count: {stat.total_word_ct}",
        "Approximate blank time: {}".format(
            hr.Time(
                str(int(stat.total_blank_secs)), default_unit=hr.Time.Unit.SECOND
            ).to_humanreadable()
        ),
        "Approximate speaking time: {}".format(
            hr.Time(
                str(int(stat.total_speak_secs)), default_unit=hr.Time.Unit.SECOND
            ).to_humanreadable()
        ),
        f"Words Per Minute: {stat.wpm:.1f}",
    ]

    for out in outputs:
        print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
