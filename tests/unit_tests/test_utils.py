# encoding: utf-8
"""
Test ``announcer.utils``.
"""
from datetime import timedelta

from announcer.utils import parse_duration


def test_parse_duration():
    """
    Test ``announcer.utils.parse_duration`` utility function
    that parses Go duration string into ``datetime.timedelta``.
    """
    # Bad formatting = 0
    assert parse_duration('nothing') == timedelta(0)
    # Partially bad formatting is OK
    assert parse_duration('10sec and 25min') == timedelta(minutes=25, seconds=10)
    # Hours
    assert parse_duration('123h') == timedelta(hours=123)
    # Minutes
    assert parse_duration('123m') == timedelta(minutes=123)
    # Seconds
    assert parse_duration('123s') == timedelta(seconds=123)
    # Milliseconds
    assert parse_duration('123ms') == timedelta(milliseconds=123)
    # Microseconds
    assert parse_duration('123us') == timedelta(microseconds=123)
    assert parse_duration(u'123µs') == timedelta(microseconds=123)
    # Nanoseconds - Python ``datetime.timedelta`` doesn't have this precision
    assert parse_duration('123ns') == timedelta(0)
    # Mix: hours, minutes, seconds
    assert parse_duration('2h 1m 15s') == timedelta(hours=2, minutes=1, seconds=15)
    # Mix: minutes, microseconds
    assert parse_duration(u'85m 00s 631µs') == timedelta(minutes=85, microseconds=631)
    # Mix: negative value
    assert parse_duration('-25h 85m') == timedelta(days=-1, hours=-2, minutes=-25)
