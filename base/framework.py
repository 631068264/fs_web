#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import random
from functools import wraps, partial

from etc import config

import flask
from attrdict import AttrDict
from base import constant as const
from base import logger
from base import smartpool
from base import util
from base.util import safe_json_dumps, url_append, encode_unicode_json, gen_uobj, to_unicode
from base.xform import FormChecker
from flask import make_response
from flask import request, redirect
from flask import url_for as base_url_for

__all__ = [
    "general",
    "app_general",

    "render_template",

    "Response",
    "JsonResponse",
    "JsonpResponse",
    "TempResponse",
    # "InfoResponse",
    "Redirect",

    "db_conn",
    "form_check",
    "url_for",

    "json_check",
    "ErrorResponse",
    "OkResponse",
]


class Response(object):
    def __init__(self):
        self._ext_header = {}
        self._ext_cookie = {}

    def set_header(self, key, value):
        self._ext_header[key] = value

    def set_cookie(self, key, value, **kwargs):
        self._ext_cookie[key] = (value, kwargs)

    def output(self):
        resp = make_response(self._output())

        for k, v in self._ext_header.iteritems():
            resp.headers[k] = v

        for k, v in self._ext_cookie.iteritems():
            resp.set_cookie(k, v[0], **v[1])

        return resp

    def _output(self):
        return "", 404


class JsonResponse(Response):
    def __init__(self, **kwargs):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "application/json"
        self._json = {} if kwargs is None else kwargs

    def _output(self):
        return safe_json_dumps(self._json)


class JsonpResponse(Response):
    def __init__(self, callback, data=None):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "text/javascript"

        self._callback = callback
        self._json = data

    def _output(self):
        return "%s(%s);" % (self._callback, safe_json_dumps(self._json))


class TempResponse(Response):
    def __init__(self, template_name, **context):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "text/html"
        self._template_name = template_name
        self._context = context

    def context_update(self, **kwargs):
        self._context.update(kwargs)

    def _output(self):
        return render_template(self._template_name, **self._context)


def render_template(name, **data):
    """
    转到模板 数据转Unicode
    :param name:
    :param data:
    :return:
    """
    udata = {}
    for k, v in data.iteritems():
        udata[to_unicode(k, config.encoding)] = gen_uobj(v, config.encoding)

    return flask.render_template(name, **udata)


# class InfoResponse(TempResponse, JsonResponse):
#     __output_pat__ = "info.html"
#     __output_var__ = "info"
#
#     def __init__(self, msg, url=None, extra=None):
#         TempResponse.__init__(self, self.__output_pat__)
#         JsonResponse.__init__(self)
#
#         resp = {self.__output_var__: msg}
#         if url is not None:
#             resp["url"] = url
#
#         if extra is not None:
#             resp["extra"] = extra
#
#         self._json = resp
#         self._context = resp.copy()
#
#     def _output(self):
#         if request.is_xhr:
#             self._ext_header["Content-Type"] = "application/json"
#             return JsonResponse._output(self)
#         self._ext_header["Content-Type"] = "text/html"
#         return TempResponse._output(self)


# class BdErrorResponse(InfoResponse):
#     __output_pat__ = "bd/error.html"
#     __output_var__ = "error"


class Redirect(JsonResponse):
    def __init__(self, url, code=302):
        JsonResponse.__init__(self)

        self._url = url
        self._code = code

    def _output(self):
        if request.cookies.get("_hotgsyd_") is not None:
            x = int(time())
            self._url = url_append(self._url, _x=x)

        if request.is_xhr:
            self._json = {"url": self._url}
            return JsonResponse._output(self)

        self._ext_header.pop("Content-Type")
        return redirect(self._url, self._code)


def db_conn(db_name_or_list_or_dict, dict_name="db_dict"):
    def deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            params = {}
            if isinstance(db_name_or_list_or_dict, dict):
                buf = {}
                for k, v in db_name_or_list_or_dict.iteritems():
                    buf[k] = smartpool.ConnectionProxy(v)
                params[dict_name] = buf

            elif isinstance(db_name_or_list_or_dict, list):
                for k in db_name_or_list_or_dict:
                    params[k] = smartpool.ConnectionProxy(k)

            else:
                k = db_name_or_list_or_dict
                params[k] = smartpool.ConnectionProxy(k)

            kwargs.update(params)
            return old_handler(*args, **kwargs)

        return new_handler

    return deco


def form_check(settings, var_name="safe_vars", strict_error=True, error_handler=None, error_var="form_errors"):
    if error_handler is None:
        error_handler = ErrorResponse

    def new_deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            req_data = {}
            for k, v in settings.iteritems():
                if v.multiple:
                    req_data[k] = request.values.getlist(k)
                else:
                    req_data[k] = request.values.get(k, None)

            checker = FormChecker(encode_unicode_json(req_data, config.encoding),
                                  settings, err_msg_encoding=config.encoding)
            if not checker.is_valid():
                if strict_error:
                    error_msg = [v for v in checker.get_error_messages().values() if v is not None]
                    return error_handler(error_msg)
                else:
                    kwargs[error_var] = checker.get_error_messages()
                    return old_handler(*args, **kwargs)

            valid_data = encode_unicode_json(checker.get_valid_data(), config.encoding)
            kwargs[var_name] = AttrDict(valid_data)

            response = old_handler(*args, **kwargs)
            if isinstance(response, TempResponse):
                response.context_update(**{var_name: valid_data})

            return response

        return new_handler

    return new_deco


def json_check(settings, var_name="safe_vars", strict_error=True, error_handler=None, error_var="form_errors"):
    u'''仅支持扁平的json
    '''
    if error_handler is None:
        error_handler = ErrorResponse

    def new_deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            try:
                values = request.get_json(force=True)
            except Exception, e:
                if config.debug:
                    raise
                return error_handler(str(e))

            req_data = {}
            for k, v in settings.iteritems():
                if v.multiple:
                    req_data[k] = values.get(k, [])
                    if isinstance(req_data[k], (list, tuple)):
                        req_data[k] = [v.encode('utf-8') if isinstance(v, unicode) else
                                       str(v) for v in req_data[k]]
                    else:
                        v = req_data[k]
                        req_data[k] = [v.encode('utf-8') if isinstance(v, unicode) else str(v)]
                else:
                    req_data[k] = values.get(k, None)
                    if req_data[k]:
                        req_data[k] = req_data[k].encode('utf-8') if isinstance(
                            req_data[k], unicode) else str(req_data[k])

            checker = FormChecker(encode_unicode_json(req_data, config.encoding),
                                  settings, err_msg_encoding=config.encoding)
            if not checker.is_valid():
                if strict_error:
                    error_msg = [v for v in checker.get_error_messages().values() if v is not None]
                    return error_handler(error_msg)
                else:
                    kwargs[error_var] = checker.get_error_messages()
                    return old_handler(*args, **kwargs)

            valid_data = encode_unicode_json(checker.get_valid_data(), config.encoding)
            kwargs[var_name] = AttrDict(valid_data)

            response = old_handler(*args, **kwargs)
            if isinstance(response, TempResponse):
                response.context_update(**{var_name: valid_data})

            return response

        return new_handler

    return new_deco


def url_for(url_rule, **kwargs):
    kwargs.setdefault('_external', True)
    return base_url_for(url_rule, **kwargs)


def general(desc, validate_sign=False):
    def deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            if validate_sign and False:
                resp = ErrorResponse(u"SIGNATURE_NOT_VALID", status=403)
            else:
                resp = old_handler(*args, **kwargs)
            if isinstance(resp, TempResponse):
                # 添加自定义变量
                resp.context_update(
                    request=request,
                    config=config,
                    const=const,
                    ver=util.get_static_file_version,
                    random=random,
                )

            if isinstance(resp, Response):
                output = resp.output()
                if config.debug:
                    logger.get("response-log").debug(
                        u"[%s] %s" % (util.to_unicode(request.url), util.to_unicode(output.data)))
                return output
            return resp

        new_handler.desc = desc
        new_handler.is_handler = True
        return new_handler

    return deco


app_general = partial(general, validate_sign=True)


class OkResponse(JsonResponse):
    def __init__(self, **kwargs):
        JsonResponse.__init__(self)

        self._json = {
            "status": const.STATUS.SUCCESS,
            "message": "",
        }
        self._json.update(kwargs)


class ErrorResponse(JsonResponse):
    def __init__(self, message, **kwargs):
        if isinstance(message, (list, tuple)):
            message = ", ".join(message)
        JsonResponse.__init__(self)

        self._json = {
            "status": const.STATUS.FAIL,
            "message": message,
        }
        self._json.update(kwargs)
