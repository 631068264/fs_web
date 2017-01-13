#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/13 19:08
@annotation = '' 
"""
from base.framework import general, db_conn, form_check, OkResponse
from base.xform import F_str
from flask import Blueprint

init = Blueprint("init", __name__)


@init.route("/index", methods=['POST'])
@general("首页")
@db_conn("db_reader")
@form_check({
    "type": F_str("请求类型") & "optional",
})
def index(db_reader, safe_vars):
    return OkResponse(type=safe_vars.type)
