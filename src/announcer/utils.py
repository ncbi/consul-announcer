# encoding: utf-8
import re
import datetime

import six


# duration units, converted to microseconds
duration_units = {
    'us': 1,  # microsecond - minimum ``datetime.timedelta`` precision
    u'µs': 1,  # microsecond - alternative notation
    'ns': 1e-3,  # nanosecond - 0.001 microseconds
    'ms': 1e3,  # millisecond - 1,000 microseconds
    's': 1e6,  # second - 1,000 milliseconds
    'm': 60 * 1e6,  # minute - 60 seconds
    'h': 60 * 60 * 1e6  # hour - 60 minutes
}


def parse_duration(s):
    """
    Parse a Go duration string into ``datetime.timedelta``.
    See https://golang.org/pkg/time/#ParseDuration.

    :param str s:
    """
    pattern = re.compile(u'(\d+(?:\.\d*)?)([numµ]?s|[mh])')
    if not isinstance(s, six.string_types):
        raise ValueError("Duration must be a string: {}".format(s))
    bits = pattern.findall(s)
    if not bits:
        raise ValueError("Duration is not parsed: {}".format(s))
    total_microseconds = 0
    sign = -1 if s[0] == '-' else 1
    for (value, unit) in bits:
        total_microseconds += float(value) * duration_units[unit]
    return datetime.timedelta(microseconds=sign * total_microseconds)
