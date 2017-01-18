#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/13 19:08
@annotation = '' 
"""

from flask import Blueprint, request

from base.framework import db_conn, OkResponse, json_check, app_general
from base.smartsql import QS, T
from base.xform import F_str

fs = Blueprint("fs", __name__)


# TODO: 接口调用安全
# TODO: 身份识别
# TODO: body 加解密

@fs.route("/register", methods=['POST'])
@app_general("fcm注册")
@db_conn("db_writer")
@json_check({
    "token": F_str("FCM_token") & "strict" & "required",
})
def index(db_writer, safe_vars):
    QS(db_writer).table(T.device).insert({
        "device_id": request.headers["X-DeviceId"],
        "token": safe_vars.token,
        "brand": request.headers["X-Brand"],
        "model": request.headers["X-Model"],
        "product": request.headers["X-Product"],
        "lang": request.headers["X-Lang"],
        "system": request.headers["X-SystemVersion"],
    }, on_duplicate_key_update={"token": safe_vars.token})
    return OkResponse()
