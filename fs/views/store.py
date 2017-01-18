#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/17 21:06
@annotation = '' 
"""
import os
from datetime import datetime

from etc import config as cfg
from flask import Blueprint, request

import base.constant as const
from base.framework import db_conn, OkResponse, app_general, ErrorResponse, form_check
from base.smartsql import QS, T
from base.xform import F_int

store = Blueprint("store", __name__)


@store.route("/picture", methods=['POST'])
@app_general("相册")
@db_conn("db_writer")
@form_check({
    "file_size": (1 <= F_int("文件数")) & "strict" & "required",
})
def picture(db_writer, safe_vars):
    is_ok, file_list = check_files("picture", safe_vars.file_size)
    if not is_ok:
        return ErrorResponse(file_list)
    device_id = request.headers["X-DeviceId"]
    save_dir = os.path.join(cfg.UPLOAD_FOLDER, device_id)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    insert_keys = ["device_id", "path", "type", "time"]
    insert_values = []
    for f in file_list:
        save_path = os.path.join(save_dir, f.filename)
        insert_values.append([
            device_id, save_path,
            const.TAKE_TYPE.PHOTOGRAPH, datetime.now()
        ])
        f.save(save_path)

    QS(db_writer).table(T.store).insert_many(insert_keys, insert_values)
    return OkResponse()


@store.route("/video", methods=['POST'])
@app_general("视频")
@db_conn("db_writer")
@form_check({
    "file_size": (1 <= F_int("文件数")) & "strict" & "required",
})
def video(db_writer, safe_vars):
    is_ok, msg = store_action(db_writer, "video", safe_vars.file_size, const.TAKE_TYPE.VIDEO)
    if not is_ok:
        return ErrorResponse(msg)
    return OkResponse()


def store_action(db, key, size, file_type):
    is_ok, file_list = check_files(key, size)
    if not is_ok:
        return False, file_list
    device_id = request.headers["X-DeviceId"]
    save_dir = os.path.join(cfg.UPLOAD_FOLDER, device_id)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    insert_keys = ["device_id", "path", "type", "time"]
    insert_values = []
    for f in file_list:
        save_path = os.path.join(save_dir, f.filename)
        insert_values.append([
            device_id,
            save_path,
            file_type,
            datetime.now()
        ])
        f.save(save_path)

    QS(db).table(T.store).insert_many(insert_keys, insert_values)
    return True, None


def check_files(key, size):
    file_key = key
    file_list = []
    for s in range(0, size):
        key = file_key + str(s)
        file_exist = key in request.files
        if not file_exist:
            return False, "没有文件"
        f = request.files[key]
        name_exist = f.filename != ""
        if not name_exist:
            return False, "文件名空"
        good_extension = '.' in f.filename and f.filename.rsplit('.', 1)[1] in cfg.ALLOWED_EXTENSIONS
        if not good_extension:
            return False, "文件类型不合"
        file_list.append(f)
    return True, file_list
