#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin

from base.util import decode_from_access_token
from base import logger


class ItsdangerousSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None):
        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.modified = False


class ItsdangerousSessionInterface(SessionInterface):
    session_class = ItsdangerousSession

    def open_session(self, app, request):
        val = request.headers.get("Authorization")
        if not val:
            return self.session_class()
        max_age = app.permanent_session_lifetime.total_seconds()
        try:
            data = decode_from_access_token(val)
            return self.session_class(data)
        except Exception, e:
            logger.error(e)
            return self.session_class()

    def save_session(self, app, session, response):
        pass
