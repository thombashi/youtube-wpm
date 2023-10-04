import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Final, List, Pattern

from ._logger import logger


ID_PATTERN: Final[str] = r"[a-zA-Z0-9_-]{11}"
RE_VIDEO_ID: Final[Pattern] = re.compile(rf"^({ID_PATTERN})$")
RE_LONG_VIDEO_URL: Final[Pattern] = re.compile(
    rf"(?<=https://www\.youtube.com/watch\?v=)({ID_PATTERN})"
)
RE_SHORT_VIDEO_URL: Final[Pattern] = re.compile(rf"(?<=https://youtu\.be/)({ID_PATTERN})")
RE_SOUND: Final[Pattern] = re.compile(r"^\[[A-Z][a-zA-Z ]+\]$")


@dataclass
class SpeakStat:
    total_word_ct: int
    total_blank_secs: Decimal
    total_speak_secs: Decimal

    @property
    def wpm(self) -> Decimal:
        return self.total_word_ct / self.total_speak_secs * 60


@dataclass(frozen=True)
class Weight:
    display_duration: Decimal
    approx_speak_time: Decimal

    @property
    def _total_wegiht(self) -> Decimal:
        return self.display_duration + self.approx_speak_time

    def calc_display_duration_weight(self) -> Decimal:
        return self.display_duration / self._total_wegiht

    def calc_approx_speak_time_weight(self) -> Decimal:
        return self.approx_speak_time / self._total_wegiht


def validate_youtube_id(value: str) -> bool:
    return RE_VIDEO_ID.match(value) is not None


def normalize_youtube_id(value: str) -> str:
    if validate_youtube_id(value):
        return value

    m = RE_LONG_VIDEO_URL.search(value)
    if m is not None:
        return m.group(1)

    m = RE_SHORT_VIDEO_URL.search(value)
    if m is not None:
        return m.group(1)

    raise ValueError(f"invalid video id: {value}")


def calc_speak_time(sequences: List[Dict], inference_spw: Decimal) -> SpeakStat:
    stat = SpeakStat(
        total_word_ct=0,
        total_blank_secs=Decimal(0),
        total_speak_secs=Decimal(0),
    )
    weight = Weight(
        display_duration=Decimal(1),
        approx_speak_time=Decimal(5),
    )
    begin_talk: Decimal = Decimal(0)
    last: Decimal = Decimal(0)
    prev_last: Decimal = Decimal(0)

    for sequence in sequences:
        text = sequence["text"].strip()
        if RE_SOUND.search(text):
            continue

        prev_last = last
        start: Decimal = Decimal(sequence["start"])

        if begin_talk == 0:
            begin_talk = start
        elif prev_last > 0:
            expected_blank_time = start - prev_last
            if expected_blank_time > 0:
                stat.total_blank_secs += start - prev_last

        # duration is how long it is displayed. As there often is some overlap between subtitle boxes
        # https://github.com/jdepoix/youtube-transcript-api/issues/21
        display_duration = Decimal(sequence["duration"])

        words = text.strip().split()
        word_ct = len(words)
        char_ct = sum([len(word) for word in words])
        words_per_duration = word_ct / display_duration
        chars_per_duration = char_ct / display_duration
        approx_speak_time = (word_ct * Decimal(0.95) + char_ct / Decimal(100)) * inference_spw
        logger.trace(
            f"{text}: {start=}, {word_ct=}, {char_ct=}, {display_duration=}, "
            f"words/d={words_per_duration:.2f}, chars/d={chars_per_duration:.2f}, "
            f"speak-time={approx_speak_time:.2f}"
        )

        last = start + (
            display_duration * weight.calc_display_duration_weight()
            + approx_speak_time * weight.calc_approx_speak_time_weight()
        )

        stat.total_word_ct += word_ct

    stat.total_speak_secs = last - begin_talk - stat.total_blank_secs

    return stat
