#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

from flask import session, request

from base import constant as const
from base.framework import Redirect
from base.framework import url_for


def login_required(roles=None):
    def new_deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            logined = session.get(const.SESSION.KEY_LOGIN)
            if logined:
                role_id = session.get(const.SESSION.KEY_ROLE_ID)
                if roles is None or role_id in roles or (isinstance(roles, int) and role_id == roles):
                    return old_handler(*args, **kwargs)
            else:
                return Redirect(url_for("home.login_load"))

        return new_handler

    return new_deco


def recognize_device(var_name="device_type"):
    def new_deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            platform = request.user_agent.platform
            kwargs[var_name] = const.DEVICE.NAME_DICT[platform]
            return old_handler(*args, **kwargs)

        return new_handler

    return new_deco
