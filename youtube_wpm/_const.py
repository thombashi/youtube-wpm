from typing import Final


EXIT_WPM_DIFF_THRESHOLD: Final[float] = 1
INITIAL_APPROXIMATE_WPM: Final[float] = 180
MAX_ITERATION: Final[int] = 10
MODULE_NAME: Final[str] = "youtube-wpm"


class Header:
    TITLE: Final = "Title"
    CHANNEL: Final = "Channel"
    TIME: Final = "Time"
    WPM: Final = "WPM"
    AUTO_GEN_TRANSCRIPT: Final = "Auto Gen Transcript"
    TOTAL_WORD_COUNT: Final = "Total word count"
    APPROXIMATE_BLANK_TIME: Final = "Approximate blank time"
    APPROXIMATE_SPEAKING_TIME: Final = "Approximate speaking time"
