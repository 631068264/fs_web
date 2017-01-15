#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/13 19:08
@annotation = '' 
"""
from attrdict import AttrDict
from etc import config as cfg
from flask import Blueprint, request

from base import util
from base.framework import db_conn, OkResponse, json_check, app_general, ErrorResponse
from base.poolmysql import transaction
from base.smartsql import QS, T, F
from base.xform import F_str, F_datetime, F_bool, FormChecker

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
        "token": safe_vars.token,
        "device_id": request.headers["X-DeviceId"],
        "brand": request.headers["X-Brand"],
        "model": request.headers["X-Model"],
        "product": request.headers["X-Product"],
        "lang": request.headers["X-Lang"],
        "system": request.headers["X-SystemVersion"],
    }, on_duplicate_key_update={"token": safe_vars.token})
    return OkResponse()


@fs.route("/get_install", methods=['POST'])
@app_general("安装程序监控")
@db_conn("db_writer")
def app_install(db_writer):
    appinfo = request.get_json(force=True)
    if not isinstance(appinfo, dict):
        return ErrorResponse("非法请求")
    is_ok, app_infos, package_names = check_install_app(appinfo, "app_info")
    if not is_ok:
        return ErrorResponse(app_infos)
    is_ok, updates, _ = check_install_app(appinfo, "update")
    if not is_ok:
        return ErrorResponse(updates)

    device_id = request.headers["X-DeviceId"]
    to_insert_keys = ["device_id", "app_name", "package_name", "version_name", "install_time"]
    with transaction(db_writer) as trans:
        installs = QS(db_writer).table(T.install).where(F.device_id == device_id).select()
        if not installs:
            QS(db_writer).table(T.install).insert_many(to_insert_keys, app_infos)
        else:
            for install in installs:
                # delete uninstall app
                if install.package_name not in package_names:
                    QS(db_writer).table(T.install).where(
                        (F.device_id == device_id) & (F.package_name == install.package_name)
                    ).delete()
        # install new app
        if updates is not None:
            QS(db_writer).table(T.install).insert_many(to_insert_keys, updates)
        trans.finish()
    return OkResponse()


@fs.route("/running", methods=['POST'])
@app_general("监控APP运行情况")
def running():
    appinfo = request.get_json(force=True)
    if not isinstance(appinfo, dict):
        return ErrorResponse("非法请求")
    is_ok, app_infos, package_names = check_install_app(appinfo, "app_info", True)
    if not is_ok:
        return ErrorResponse(app_infos)
    device_id = request.headers["X-DeviceId"]
    if appinfo:
        print appinfo
    return OkResponse(appinfo=appinfo)


def check_install_app(appinfo, key, running=False):
    if not appinfo.get(key):
        return True, None, None
    device_id = request.headers["X-DeviceId"]
    check_settings = {
        "app_name": (F_str("应用名") <= 128) & "strict" & "required",
        "package_name": (F_str("包名") <= 255) & "strict" & "required",
        "version_name": (F_str("版本名") <= 64) & "optional",
        "install_time": F_datetime("安装时间") & "optional",
        "run_time": (F_str("运行时间") <= 64) & "optional",
        "is_foreground": F_bool("是否在前台运行") & "optional",
    }
    valid_vars = []
    for app_info in appinfo.get(key):
        check = FormChecker(util.encode_unicode_json(app_info, cfg.encoding),
                            check_settings, err_msg_encoding=cfg.encoding)
        if not check.is_valid():
            error_msg = [v for v in check.get_error_messages().values() if v is not None]
            return False, error_msg, None
        valid_vars.append(AttrDict(util.encode_unicode_json(check.get_valid_data(), cfg.encoding)))
    if running:
        return True, valid_vars, None
    insert_values = []
    package_names = []
    for valid_var in valid_vars:
        insert_values.append([
            device_id, valid_var["app_name"],
            valid_var["package_name"], valid_var["version_name"],
            valid_var["install_time"],
        ])
        package_names.append(valid_var["package_name"])
    return True, insert_values, package_names
