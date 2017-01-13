#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import sys
import re

from jinja2 import evalcontextfilter, Markup, escape

from etc import config
from base import smartpool, poolmysql
from base.client_session import ItsdangerousSessionInterface
from base.framework import url_for, ErrorResponse
from base import logger
from base.cache import cache


def init(app):
    # log setting
    logger.init_log([(n, os.path.join("logs", p), l)
                     for n, p, l in config.log_config])

    # pool setting
    smartpool.coroutine_mode = config.pool_coroutine_mode
    if config.debug and getattr(config, "pool_log", None) is not None:
        smartpool.pool_logger = logger.get(config.pool_log).info

    # mysql setting
    if config.debug and getattr(config, "db_query_log", None) is not None:
        poolmysql.query_logger = logger.get(config.db_query_log).info

    for name, setting in config.db_config.iteritems():
        smartpool.init_pool(
            name, setting, poolmysql.MySQLdbConnection, *config.db_conn_pool_size,
            maxidle=config.db_connection_idle, clean_interval=config.db_pool_clean_interval
        )

    app.debug = config.debug
    app.config.update(config.app_config)

    # cache
    cache.init_app(app)

    # # redis session
    # app.session_interface = RedisSessionInterface(redis.StrictRedis(
    #     connection_pool=redis.ConnectionPool()))

    app.session_interface = ItsdangerousSessionInterface()

    # reg filters
    from base import jinja_filter
    for name, func in jinja_filter.mapping.iteritems():
        app.template_filter(name)(func)

    app.jinja_env.globals['url_for'] = url_for

    # reg exception handler
    @app.errorhandler(500)
    def handle_500(error):
        import traceback
        error_str = traceback.format_exc()
        logger.get("cgi-log").error(error_str)

        if config.debug:
            return error

        msg = error_str if config.debug else "系统异常"
        return ErrorResponse(msg).output(), 200

    @app.errorhandler(Exception)
    def handle_exception(error):
        import traceback
        error_str = traceback.format_exc()
        logger.get("cgi-log").error(error_str)

        if config.debug:
            from flask._compat import reraise
            handler = app.error_handler_spec[None].get(Exception)
            exc_type, exc_value, tb = sys.exc_info()
            reraise(exc_type, exc_value, tb)

        msg = error_str if config.debug else "系统异常"
        return ErrorResponse(msg).output(), 200

    @app.errorhandler(404)
    def page_not_found(error):
        return ErrorResponse('Not Found').output(), 404

    @app.errorhandler(405)
    def method_not_allow(error):
        return ErrorResponse(str(error)).output(), 405

    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

    @app.template_filter()
    @evalcontextfilter
    def nl2br(eval_ctx, value):
        result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br/>\n'))
                              for p in _paragraph_re.split(escape(value)))
        if eval_ctx.autoescape:
            result = Markup(result)
        return result
