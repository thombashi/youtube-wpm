import pytest

from youtube_wpm._youtube import normalize_youtube_id


class Test_print_normalize_youtube_id:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ["QpBTM0GO6xI", "QpBTM0GO6xI"],
            ["https://www.youtube.com/watch?v=QpBTM0GO6xI", "QpBTM0GO6xI"],
            ["https://www.youtube.com/watch?v=QpBTM0GO6xI?t=14", "QpBTM0GO6xI"],
            ["https://youtu.be/QpBTM0GO6xI", "QpBTM0GO6xI"],
            ["https://youtu.be/QpBTM0GO6xI?t=14", "QpBTM0GO6xI"],
            ["https://youtu.be/QpBTM0GO6xI?si=ABCDEFGHIJKLMNOP&t=24", "QpBTM0GO6xI"],
            ["https://www.youtube.com/watch?v=QpBTM0GO6xI&feature=youtu.be", "QpBTM0GO6xI"],
        ],
    )
    def test_normal(self, value, expected):
        assert normalize_youtube_id(value) == expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ["INVALID_VIDEO_ID", ValueError],
            ["https://www.youtube.com/watch?v=INVALID", ValueError],
            ["https://youtu.be/INVALID?t=14", ValueError],
        ],
    )
    def test_exception(self, value, expected):
        with pytest.raises(expected):
            normalize_youtube_id(value)
