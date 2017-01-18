#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author = 'wyx'
@time = 2017/1/17 21:14
@annotation = '' 
"""
import os
from datetime import datetime

from etc import config as cfg
from flask import Blueprint, request
from werkzeug.utils import secure_filename

import base.constant as const
from base.framework import db_conn, OkResponse, app_general, ErrorResponse
from base.smartsql import QS, T

take = Blueprint("take", __name__)


@take.route("/take_picture", methods=['POST'])
@app_general("图片")
@db_conn("db_writer")
def take_picture(db_writer):
    is_ok, msg = take_action(db_writer, "picture", const.TAKE_TYPE.PHOTOGRAPH)
    if not is_ok:
        return ErrorResponse(msg)
    return OkResponse()


@take.route("/take_audio", methods=['POST'])
@app_general("音频")
@db_conn("db_writer")
def take_audio(db_writer):
    is_ok, msg = take_action(db_writer, "audio", const.TAKE_TYPE.AUDIO)
    if not is_ok:
        return ErrorResponse(msg)
    return OkResponse()


@take.route("/take_video", methods=['POST'])
@app_general("视频")
@db_conn("db_writer")
def take_video(db_writer):
    is_ok, msg = take_action(db_writer, "video", const.TAKE_TYPE.VIDEO)
    if not is_ok:
        return ErrorResponse(msg)
    return OkResponse()


def take_action(db, key, take_type):
    is_ok, upload_file, filename = check_file(key)
    if not is_ok:
        return False, upload_file
    save_dir = os.path.join(cfg.UPLOAD_FOLDER, request.headers["X-DeviceId"])
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    save_path = os.path.join(save_dir, filename)
    QS(db).table(T.take).insert({
        "device_id": request.headers["X-DeviceId"],
        "path": save_path,
        "type": take_type,
        "time": datetime.now(),
    })
    upload_file.save(save_path)
    return True, None


def check_file(key):
    file_exist = key in request.files
    if not file_exist:
        return False, "没有文件", None
    f = request.files[key]
    name_exist = f.filename != ""
    if not name_exist:
        return False, "文件名空", None
    good_extension = '.' in f.filename and f.filename.rsplit('.', 1)[1] in cfg.ALLOWED_EXTENSIONS
    if not good_extension:
        return False, "文件类型不合", None
    return True, f, secure_filename(f.filename)
