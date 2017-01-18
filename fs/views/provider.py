#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/17 21:19
@annotation = '' 
"""

from flask import Blueprint, request

import base.constant as const
from base import util
from base.framework import db_conn, OkResponse, app_general, ErrorResponse
from base.poolmysql import transaction
from base.smartsql import QS, T
from base.xform import F_str, F_datetime, F_int

provider = Blueprint("provider", __name__)


@provider.route("/call", methods=['POST'])
@app_general("通话记录")
@db_conn("db_writer")
def call(db_writer):
    call_info = request.get_json(force=True)
    if not isinstance(call_info, dict):
        return ErrorResponse("非法请求")
    is_ok, insert_values = check_call(call_info, "call")
    if not is_ok:
        return ErrorResponse(insert_values)
    insert_keys = ["device_id", "name", "phone_number", "time", "duration", "type"]
    if call_info:
        with transaction(db_writer) as trans:
            QS(db_writer).table(T.call_record).insert_many(insert_keys, insert_values)
            trans.finish()
    return OkResponse()


def check_call(call_info, key):
    if not call_info.get(key):
        return False, "非法请求"
    device_id = request.headers["X-DeviceId"]
    check_settings = {
        "name": (F_str("联系人名") <= 15) & "optional",
        "phone_number": (F_str("手机号") <= 20) & "strict" & "required",
        "time": F_datetime("通话时间") & "strict" & "required",
        "duration": F_str("通话时长") & "strict" & "required",
        "type": F_int("通话类型") & "strict" & "required" & (lambda v: (v in const.CALL_TYPE.ALL, v)),
    }
    is_ok, valid_vars = util.valid_var(call_info.get(key), check_settings)
    if not is_ok:
        return False, valid_vars
    insert_values = []
    for valid_var in valid_vars:
        insert_values.append([
            device_id, valid_var["name"],
            valid_var["phone_number"], valid_var["time"],
            valid_var["duration"], valid_var["type"],
        ])
    return True, insert_values


@provider.route("/contact", methods=['POST'])
@app_general("联系人记录")
@db_conn("db_writer")
def contact(db_writer):
    contact_info = request.get_json(force=True)
    if not isinstance(contact_info, dict):
        return ErrorResponse("非法请求")
    is_ok, insert_values = check_contact(contact_info, "contact")
    if not is_ok:
        return ErrorResponse(insert_values)
    insert_keys = ["device_id", "name", "phone_number"]
    if contact_info:
        with transaction(db_writer) as trans:
            QS(db_writer).table(T.contact_record).insert_many(insert_keys, insert_values)
            trans.finish()
    return OkResponse()


def check_contact(contact_info, key):
    if not contact_info.get(key):
        return False, "非法请求"
    device_id = request.headers["X-DeviceId"]
    check_settings = {
        "name": (F_str("联系人名") <= 15) & "optional",
        "phone_number": F_str("手机号") & "strict" & "required",
    }
    is_ok, valid_vars = util.valid_var(contact_info.get(key), check_settings)
    if not is_ok:
        return False, valid_vars
    insert_values = []
    for valid_var in valid_vars:
        insert_values.append([
            device_id, valid_var["name"],
            valid_var["phone_number"],
        ])
    return True, insert_values


@provider.route("/sms", methods=['POST'])
@app_general("短信记录")
@db_conn("db_writer")
def sms(db_writer):
    sms_info = request.get_json(force=True)
    if not isinstance(sms_info, dict):
        return ErrorResponse("非法请求")
    is_ok, insert_values = check_sms(sms_info, "sms_all")
    if not is_ok:
        return ErrorResponse(insert_values)
    insert_keys = ["device_id", "name", "phone_number", "time", "content"]
    if sms_info:
        with transaction(db_writer) as trans:
            QS(db_writer).table(T.sms_record).insert_many(insert_keys, insert_values)
            trans.finish()
    return OkResponse()


def check_sms(sms_info, key):
    if not sms_info.get(key):
        return False, "非法请求"
    device_id = request.headers["X-DeviceId"]
    check_settings = {
        "name": (F_str("联系人名") <= 15) & "optional",
        "phone_number": (F_str("手机号") <= 20) & "strict" & "required",
        "time": F_datetime("时间") & "strict" & "required",
        "content": F_str("短信内容") & "strict" & "required",
    }
    is_ok, valid_vars = util.valid_var(sms_info.get(key), check_settings)
    if not is_ok:
        return False, valid_vars
    insert_values = []
    for valid_var in valid_vars:
        insert_values.append([
            device_id, valid_var["name"],
            valid_var["phone_number"], valid_var["time"],
            valid_var["content"],
        ])
    return True, insert_values
