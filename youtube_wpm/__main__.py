import argparse
import sys
from decimal import Decimal
from itertools import chain
from textwrap import dedent
from typing import Final, List, Literal

import humanreadable as hr
import pytablewriter as ptw
from pytube import Channel, YouTube
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from .__version__ import __version__
from ._const import (
    EXIT_WPM_DIFF_THRESHOLD,
    INITIAL_APPROXIMATE_WPM,
    MAX_ITERATION,
    MODULE_NAME,
    Header,
)
from ._logger import LogLevel, initialize_logger, logger
from ._youtube import SpeakStats, calc_speak_time, make_youtube_url, normalize_youtube_id


OutputFormat = Literal["markdown", "md-table"]


def parse_option() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
    parser.add_argument("video_id_list", metavar="VIDEO_ID", nargs="+", help="YouTube video IDs")

    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", dest="verbosity_level", action="count", default=0)

    parser.add_argument(
        "--language",
        default="en",
        help="language code of the transcript",
    )
    parser.add_argument(
        "--initial-wpm",
        type=float,
        default=INITIAL_APPROXIMATE_WPM,
        help="initial approximate words per minute",
    )

    group = parser.add_argument_group("Output Format")
    group.add_argument(
        "--format",
        dest="output_format",
        default="markdown",
        choices=["markdown", "md-table"],
        help="output format",
    )
    group.add_argument(
        "--length-format",
        default="short",
        choices=["short", "long"],
        help="output format of the video length",
    )

    loglevel_dest = "log_level"
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--debug",
        dest=loglevel_dest,
        action="store_const",
        const=LogLevel.DEBUG,
        default=LogLevel.INFO,
        help="for debug print",
    )
    group.add_argument(
        "--quiet",
        dest=loglevel_dest,
        action="store_const",
        const=LogLevel.QUIET,
        default=LogLevel.INFO,
        help="suppress execution log messages",
    )

    return parser.parse_args()


def calc_seconds_per_word(wpm: Decimal) -> Decimal:
    return 60 / wpm


def normalize_languages(language: str) -> List[str]:
    if language in ("en", "en-US"):
        return ["en-US", "en"]

    return [language]


def extract_outputs(
    output_format: OutputFormat,
    yt: YouTube,
    channel: Channel,
    speak_stats: SpeakStats,
    length_format: str,
    is_generated_transcript: bool,
    verbosity_level: int,
) -> List[str]:
    video_id: Final[str] = yt.vid_info["videoDetails"]["videoId"]
    title_link: Final = f"[{yt.title}]({make_youtube_url(video_id)})"
    channel_link: Final = f"[{channel.channel_name}]({yt.channel_url})"
    wpm: Final = f"{speak_stats.wpm:.1f}"
    video_length: Final[str] = hr.Time(
        str(yt.length), default_unit=hr.Time.Unit.SECOND
    ).to_humanreadable(style=length_format)
    approx_blank_time: Final[str] = hr.Time(
        str(int(speak_stats.total_blank_secs)), default_unit=hr.Time.Unit.SECOND
    ).to_humanreadable(style=length_format)
    approx_speaking_time: Final[str] = hr.Time(
        str(int(speak_stats.total_speak_secs)), default_unit=hr.Time.Unit.SECOND
    ).to_humanreadable(style=length_format)

    assert speak_stats.total_speak_secs > 0

    if output_format == "markdown":
        outputs = [
            f"- {Header.TITLE}: {title_link}",
            f"- {Header.CHANNEL}: {channel_link}",
            f"- {Header.TIME}: {video_length}",
            f"- {Header.WPM}: {wpm}",
            f"- {Header.AUTO_GEN_TRANSCRIPT}: {is_generated_transcript}",
        ]
        if verbosity_level > 0:
            outputs.extend(
                [
                    f"- {Header.TOTAL_WORD_COUNT}: {speak_stats.total_word_ct}",
                    f"- {Header.APPROXIMATE_BLANK_TIME}: {approx_blank_time}",
                    f"- {Header.APPROXIMATE_SPEAKING_TIME}: {approx_speaking_time}",
                ]
            )
        outputs.append("")
    elif output_format == "md-table":
        outputs = [
            title_link,
            channel_link,
            video_length,
            wpm,
            str(is_generated_transcript),
        ]
        if verbosity_level > 0:
            outputs.extend(
                [
                    str(speak_stats.total_word_ct),
                    approx_blank_time,
                    approx_speaking_time,
                ]
            )
    else:
        raise ValueError(f"unknown output format: {output_format}")

    return outputs


def render_outputs(
    output_format: OutputFormat, output_matrix: List[List[str]], verbosity_level: int
) -> None:
    if output_format == "markdown":
        for line in chain.from_iterable(output_matrix):
            print(line)
    elif output_format == "md-table":
        base_headers: Final = [
            Header.TITLE,
            Header.CHANNEL,
            Header.TIME,
            Header.WPM,
            Header.AUTO_GEN_TRANSCRIPT,
        ]

        if verbosity_level == 0:
            headers = base_headers
        else:
            headers = base_headers + [
                Header.TOTAL_WORD_COUNT,
                Header.APPROXIMATE_BLANK_TIME,
                Header.APPROXIMATE_SPEAKING_TIME,
            ]
        ptw.MarkdownTableWriter(
            headers=headers,
            value_matrix=output_matrix,
            margin=1,
        ).write_table()
    else:
        raise ValueError(f"unknown output format: {output_format}")


def main() -> int:
    ns = parse_option()

    initialize_logger(name=MODULE_NAME, log_level=ns.log_level)

    initial_wpm: Final = Decimal(ns.initial_wpm)

    return_value = 0
    output_matrix: List[List[str]] = []
    for video_id in ns.video_id_list:
        video_id = normalize_youtube_id(video_id)
        logger.debug(f"fetching transcripts of {video_id=} ...")

        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        except TranscriptsDisabled as e:
            logger.error(e)
            return_value = 1
            continue

        try:
            transcript = transcripts.find_transcript(normalize_languages(ns.language))
        except NoTranscriptFound as e:
            logger.error(e)
            return_value = 1
            continue

        logger.debug(
            f"calculating wpm: {video_id=}, {transcript.language=}, {transcript.language_code=}, "
            f"{transcript.is_generated=}"
        )

        prev_wpm: Decimal = initial_wpm
        inference_spw = calc_seconds_per_word(prev_wpm)

        sequences = transcript.fetch()
        for i in range(MAX_ITERATION):
            stats = calc_speak_time(sequences, inference_spw=inference_spw)
            diff_wpm = abs(stats.wpm - prev_wpm)
            logger.debug(f"iteration={i}, wpm={stats.wpm:.1f}, diff_wpm={diff_wpm:.1f}")
            if diff_wpm < EXIT_WPM_DIFF_THRESHOLD:
                break

            inference_spw = calc_seconds_per_word(stats.wpm)
            prev_wpm = stats.wpm

        logger.debug(f"fetching vido info of {video_id} ...")
        yt = YouTube.from_id(video_id)
        output_matrix.append(
            extract_outputs(
                output_format=ns.output_format,
                yt=yt,
                channel=Channel(yt.channel_url),
                speak_stats=stats,
                length_format=ns.length_format,
                is_generated_transcript=transcript.is_generated,
                verbosity_level=ns.verbosity_level,
            )
        )

    render_outputs(ns.output_format, output_matrix, verbosity_level=ns.verbosity_level)

    return return_value


if __name__ == "__main__":
    sys.exit(main())
