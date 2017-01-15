#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import calendar
import datetime
import hashlib
import os
import re
import socket
import struct
import urllib
import urlparse
from base64 import b64encode, b64decode
from decimal import Decimal

import jwt
import simplejson as json
from Crypto.Cipher import AES
from attrdict import AttrDict
from etc import config
from flask import current_app
from html2text import HTML2Text

from base import logger
from base.cache import cache


def split_list(lst, n_part):
    "not keep continuess"
    return [lst[i::n_part] for i in xrange(n_part)]


def text2html(text):
    return '<p>%s</p>' % (text.replace('\r', '')
                          .replace('\n\n', '</p><p>')
                          .replace('\n', '<br/>')
                          .replace(' ', '&nbsp;'))


def safe_json_default(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, Decimal):
        return float(obj)

    return str(obj)


def safe_json_dumps(obj, encoding=None, silent=True):
    """
    Encode a Python object to JSON formatted string.

    @params object: Python object
    @params encoding: the character encoding for str instances, default is UTF-8.
    @params silent: not raise error, default is True

    @return: a JSON formatted string if dumps success or None

    """
    kwargs = {"default": safe_json_default}
    if encoding is not None:
        kwargs["encoding"] = encoding

    try:
        str = json.dumps(obj, **kwargs)
    except (ValueError, TypeError):
        if silent:
            return None
        raise

    return str


def safe_inet_ntoa(n):
    """
    Convert numerical ip to string ip(like: 2071801890 -> "123.125.48.34"),
    return None if failed.
    """
    try:
        ip = socket.inet_ntoa(struct.pack(">L", n))
    except (struct.error, socket.error):
        return None

    return ip


def safe_inet_aton(ip):
    """
    Convert string ip to numerical ip(like: "123.125.48.34" -> 2071801890),
    return None if failed.
    """
    try:
        n = struct.unpack(">L", socket.inet_pton(socket.AF_INET, ip))[0]
    except (struct.error, socket.error, AttributeError):
        return None

    return n


def get_day_begin_time(time=None):
    """
    @params time: datatime

    @return: datetime, begin time of a day
    """
    if not time:
        time = datetime.datetime.now()
    return time.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end_time(time):
    """
    @params time: datetime

    @return: datetime, end time of a day
    """
    return time.replace(hour=23, minute=59, second=59, microsecond=0)


def get_week_begin_time(time=None):
    """
    @params time: datetime

    @return: datetime, begin time of a week
    """
    if time is None:
        time = datetime.datetime.now()
    return (time - datetime.timedelta(days=time.weekday())).replace(hour=0, minute=0, second=0)


def get_week_end_time(time=None):
    """
    @params time: datetime

    @return: datetime, end time of a week
    """
    if time is None:
        time = datetime.datetime.now()
    return (time + datetime.timedelta(days=6 - time.weekday())).replace(hour=23, minute=59, second=59)


def get_month_begin_time(time=None):
    if time is None:
        time = datetime.datetime.now()
    return (time - datetime.timedelta(days=int(time.strftime('%d')) - 1)).replace(hour=0, minute=0, second=0)


def get_month_end_time(time=None):
    if time is None:
        time = datetime.datetime.now()
    today_in_month = int(time.strftime('%d'))
    day_of_month = calendar.monthrange(int(time.strftime('%Y')), int(time.strftime('%m')))[1]
    return (time + datetime.timedelta(days=day_of_month - today_in_month)).replace(hour=0, minute=0, second=0)


def str_to_time(str_date, format="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.datetime.strptime(str_date, format)
    except:
        return datetime.datetime.now()


def safe_strpdate(data):
    parsed = str_to_time(data, "%Y-%m-%d")
    return None if parsed is None else parsed.date()


def url_append(url, nodup=True, **kwargs):
    old_params = urlparse.urlparse(url)[4]
    if nodup and old_params:
        buf = urlparse.parse_qs(old_params)
        for k in buf:
            if k in kwargs:
                kwargs.pop(k)

    if len(kwargs) < 1:
        return url

    params = urllib.urlencode(kwargs)
    if old_params:
        return url + "&" + params
    else:
        return url + "?" + params


def encode_unicode_json(obj, encoding):
    """
    Translate unicode obj into local encoding, usage may be:
      1. json loads return a obj which all str is unicode, encode it to our encoding.
      2. other json like obj can use this func too. ex: form_check
    """

    if isinstance(obj, unicode):
        return obj.encode(encoding)
    elif isinstance(obj, list):
        return [encode_unicode_json(v, encoding) for v in obj]
    elif isinstance(obj, dict):
        return dict([(encode_unicode_json(k, encoding), encode_unicode_json(v, encoding))
                     for k, v in obj.iteritems()])

    return obj


def to_unicode(data, encoding="utf-8"):
    """convert data from some encoding to unicode
    data could be string, list, tuple or dict
    that contains string as key or value
    """
    if data is None:
        return unicode('')

    if isinstance(data, unicode):
        return data

    if isinstance(data, (list, tuple)):
        u_data = []
        for item in data:
            u_data.append(to_unicode(item, encoding))

    elif isinstance(data, dict):
        u_data = {}
        for key in data:
            u_data[to_unicode(key, encoding)] = to_unicode(data[key], encoding)

    elif isinstance(data, str):
        u_data = unicode(data, encoding, 'ignore')
    else:
        u_data = data

    return unicode(u_data)


class UObj:
    # do not gen UObj when input obj type is in base_types
    base_types = (
        bool, float, int, long, complex, unicode,
    )
    # do not gen UObj when attr name in raw_attrs
    raw_attrs = (
        '__name__', '__coerce__',
    )
    # gen UObj with fake rop when input obj doesn't have the attr and
    # attr is in rops
    rops = (
        '__radd__', '__rdiv__', '__rmod__', '__rmul__', '__rsub__',
        '__rand__', '__rlshift__', '__ror__', '__rrshift__', '__rxor__',
        '__rdivmod__', '__rpow__',
    )

    def __init__(self, obj, encoding, fake_rop):
        self._obj = obj
        self._encoding = encoding
        self._fake_rop = fake_rop

    @classmethod
    def _gen_rop_name(self, name):
        """
        gen fake rop name, just removing the first 'r' in original name
        """
        return name.replace('r', '', 1)

    @classmethod
    def _cvt_arg(self, arg):
        """
        single argument conversion, return internal obj if arg is an UObj instance
        """
        if isinstance(arg, UObj):
            return arg._obj
        return arg

    @classmethod
    def _cvt_args(self, *args):
        """
        sequence argument conversion
        """
        return [UObj._cvt_arg(a) for a in args]

    @classmethod
    def _cvt_kwargs(self, **kwargs):
        """
        keyword argument conversion
        """
        new_kwargs = {}
        for key, value in kwargs.iteritems():
            new_kwargs[UObj._cvt_arg(key)] = UObj._cvt_arg(value)
        return new_kwargs

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __cmp__(self, other):
        other = UObj._cvt_arg(other)
        if self._obj == other:
            return 0
        elif self._obj > other:
            return 1
        else:
            return -1

    def __unicode__(self):
        return to_unicode(self._obj, self._encoding)

    def __getattr__(self, name):
        fake_rop = False
        if (not hasattr(self._obj, name)) and (name in UObj.rops):
            new_name = UObj._gen_rop_name(name)
            if hasattr(self._obj, new_name):
                name = new_name
                fake_rop = True
        attr = getattr(self._obj, name)
        if name in UObj.raw_attrs:
            return attr
        return gen_uobj(attr, self._encoding, fake_rop)

    def __call__(self, *args, **kwargs):
        if self._fake_rop:
            return gen_uobj(getattr(args[0], self.__name__)(self._obj.__self__), self._encoding)
        return gen_uobj(self._obj(*(UObj._cvt_args(*args)), **(UObj._cvt_kwargs(**kwargs))),
                        self._encoding)

    def origin(self):
        return self._obj


def gen_uobj(obj, encoding="utf-8", fake_rop=False):
    """
    转成Unicode
    :param obj:
    :param encoding:
    :param fake_rop:
    :return:
    """
    if isinstance(obj, str):
        return obj.decode(encoding, 'ignore')

    if not obj or isinstance(obj, UObj.base_types):
        return obj

    return UObj(obj, encoding, fake_rop)


def html2text(html):
    html2text_handler = HTML2Text()
    html2text_handler.ignore_images = True
    html2text_handler.ignore_links = True
    text = html2text_handler.handle(to_unicode(html))
    return text


def text_filter(text):
    u'''
    过滤：
    1. 论坛
    2. 转载自：
    3. 私服
    4. 微信公众号
    5. 新浪微博
    6. 所有的链接
    '''

    text = to_unicode(text)

    words = [
        u"论坛",
        u"转载自：",
        u"私服",
        u"微信公众号",
        u"新浪微博",
        u"微博",
        u"微信号",
        u"微信",
        u"我是男的",
    ]

    for word in words:
        text = text.replace(word, "")

    # 过滤网址
    text = re.sub(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", "", text)
    text = re.sub(r"www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", "", text)
    # 过滤QQ
    text = re.sub(r"QQ[0-9]+", "", text)

    return text


def md5(content):
    return hashlib.md5(content).hexdigest()


def hash_password(password, username):
    return hashlib.md5("%s%s%s" % (username, password, username)).hexdigest()


key = "VymiluoOWUL6twaK"


def encrypt(target):
    u"""加密一个字符串

    secret: 密钥，长度需要为16个字节
    代码来自: https://gist.github.com/sekondus/4322469
    """

    # the block size for the cipher object; must be 16, 24, or 32 for AES
    BLOCK_SIZE = 16

    # the character used for padding--with a block cipher such as AES, the value
    # you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
    # used to ensure that your value is always a multiple of BLOCK_SIZE
    PADDING = '{'

    # create a cipher object using the random secret
    cipher = AES.new(key)
    return b64encode(cipher.encrypt(target + (
        BLOCK_SIZE - len(target) % BLOCK_SIZE) * PADDING))


def decrypt(target):
    u"""解密用encrypt加密的字符串

    secret: 密钥，长度需要为16个字节
    """

    PADDING = '{'
    cipher = AES.new(key)
    raw = cipher.decrypt(b64decode(target))
    return raw[:(raw.rfind(PADDING) + 1)].rstrip(PADDING)


def convert_underscore2camelcase(word):
    s = ''.join(x.capitalize() or '_' for x in word.split('_'))
    s = s[0].lower() + s[1:]
    return s


def convert_dict_key_underscore2camelcase(d):
    if not d:
        return d
    attr_dict = AttrDict()
    for k, v in d.iteritems():
        attr_dict[convert_underscore2camelcase(k)] = d[k]
    return attr_dict


def convert_list_underscore2camelcase(l):
    return [convert_dict_key_underscore2camelcase(i) for i in l]


def sha1OfFile(filepath):
    sha = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            block = f.read(2 ** 10)  # Magic number: one-megabyte blocks.
            if not block:
                break
            sha.update(block)
        return sha.hexdigest()


def gen_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365),
        'nbf': datetime.datetime.utcnow(),
    }

    try:
        return jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
    except Exception, e:
        logger.error(e)
        return ""


def decode_from_access_token(encoded):
    d = {}
    if encoded:
        try:
            d = jwt.decode(encoded, config.JWT_SECRET, algorithms=['HS256'])
        except Exception, e:
            logger.get("auth").error(e)
    return AttrDict(d if d else {})


def get_weekname(dt):
    d = (u"周一", u"周二", u"周三", u"周四", u"周五", u"周六", u"周日")
    return d[dt.weekday()]


@cache.memoize(config.cache_memorized_timeout)
def get_static_file_version(full_filename):
    filename = os.path.join(current_app.static_folder, full_filename)
    sha1 = sha1OfFile(filename)
    return sha1
