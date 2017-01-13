#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    custom filters for jinja2
"""

import time
import string
import random
import urllib
import functools

import util
from etc import config


def _force_str(s):
    """
    convert s to <type 'str'>, if s is <type 'unicode'>
    """
    if isinstance(s, unicode):
        s = s.encode(config.default_encoding)
    return s


def format_datetime(value, format="%Y-%m-%d %H:%M:%S", default=""):
    if value is None:
        return default
    return value.strftime(_force_str(format))


def format_null(value, default=""):
    if value is None:
        return default
    return value


def format_ratio(value, precision=2, is_percent=False, default=""):
    if value is None:
        return default
    if is_percent:
        value = value * 100
    format = "%%.%df" % precision
    return format % value


def fen2yuan(value, default=""):
    if value is None:
        return default
    return "%.2f" % (int(value) / 100.0)


def inet_ntoa(value, default=""):
    if value is None:
        return default
    return util.safe_inet_ntoa(value)


def mktime(value):
    return time.mktime(value.timetuple())


def urlencode(value):
    if value is None:
        return None
    return urllib.quote(value)


def killcache(value, length):
    _id = ''.join(random.choice(string.lowercase) for i in range(length))
    if value.rfind("?") < 0:
        return "%s?_id=%s" % (value, _id)
    else:
        return "%s&_id=%s" % (value, _id)


def html2text(value):
    return util.html2text(value)


def text_filter(value):
    return util.text_filter(value).strip()


def limit_str_len(value, max_len=10, tail_len=0):
    if tail_len > 0 and len(value) > max_len + tail_len:
        return value[:max_len] + "....." + value[-tail_len:]
    if len(value) > max_len:
        return value[:max_len] + "..."
    return value


def weekname(value):
    return util.get_weekname(value)


def format_json(value):
    return util.safe_json_dumps(util.LOCAL.REALM + value, encoding='utf-8')


# mapping

mapping = {
    "fm_time": functools.partial(format_datetime, format="%H:%M:%S", default='-'),
    "fm_date": functools.partial(format_datetime, format="%Y-%m-%d", default='-'),
    "fm_datetime": format_datetime,
    "fm_null": format_null,
    "fm_json": format_json,
    "fm_ratio": format_ratio,
    "fen2yuan": fen2yuan,
    "inet_ntoa": inet_ntoa,
    "mktime": mktime,
    "urlencode": urlencode,
    "killcache": killcache,
    "html2text": html2text,
    "text_filter": text_filter,
    "limit_str_len": limit_str_len,
    "weekname": weekname,
}
