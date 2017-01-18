#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/17 21:06
@annotation = '' 
"""

from flask import Blueprint, request

from base import util
from base.framework import db_conn, OkResponse, app_general, ErrorResponse
from base.poolmysql import transaction
from base.smartsql import QS, T, F
from base.xform import F_str, F_datetime, F_bool

appinfo = Blueprint("appinfo", __name__)


@appinfo.route("/get_install", methods=['POST'])
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


@appinfo.route("/running", methods=['POST'])
@app_general("监控APP运行情况")
def running():
    appinfo = request.get_json(force=True)
    if not isinstance(appinfo, dict):
        return ErrorResponse("非法请求")
    is_ok, app_infos, package_names = check_install_app(appinfo, "app_info", True)
    if not is_ok:
        return ErrorResponse(app_infos)
    device_id = request.headers["X-DeviceId"]
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
    is_ok, valid_vars = util.valid_var(appinfo.get(key), check_settings)
    if not is_ok:
        return False, valid_vars, None
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
