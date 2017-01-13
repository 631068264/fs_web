#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'wuyuxi'
import os
import random
from cStringIO import StringIO

from captcha.image import ImageCaptcha

from flask import Blueprint, session, redirect, send_file, send_from_directory
import qrcode

from base import logger as log, util, constant as const
from base.framework import general, TempResponse, url_for, form_check, db_conn, ErrorResponse, OkResponse
from base.decorator import login_required, recognize_device
from base import dao
from base.poolmysql import transaction, lock_str
from base.xform import F_str

home = Blueprint("home", __name__)


@home.route("/app")
@general("app主页界面")
@login_required()
@recognize_device()
def app_index(device_type):
    if device_type == const.DEVICE.NAME_DICT[const.DEVICE.WINDOWS]:
        return redirect(url_for("home.index"))
    return TempResponse(device_type + "/index.html")


@home.route("/")
@home.route("/index")
@general("主页界面")
@recognize_device()
def index(device_type):
    return TempResponse(device_type + "/index.html")


@home.route("/login/load")
@general("登录界面")
@recognize_device()
def login_load(device_type):
    if session.get(const.SESSION.KEY_LOGIN):
        if device_type == const.DEVICE.NAME_DICT[const.DEVICE.ANDOID]:
            return redirect(url_for("home.app_index"))
        return redirect(url_for("home.index"))
    return TempResponse(device_type + "/login.html")


@home.route("/register/load")
@general('注册页面')
@recognize_device()
def register_load(device_type):
    return TempResponse(device_type + "/register.html")


@home.route("/register", methods=['POST'])
@general('注册')
@db_conn('db_writer')
@form_check({
    "username": F_str("用户名") & "strict" & "required",
    "password": F_str("密码") & "strict" & "required",
})
def register(db_writer, safe_vars):
    with lock_str(db_writer, "register_account.%s" % (safe_vars.username,)) as locked:
        if not locked:
            log.error("register_account lock failed ,[%s]" % (safe_vars.username,))
            return ErrorResponse("系统繁忙，请稍后再试")
        account = dao.get_account_by_username(db_writer, safe_vars.username)
        if account:
            return ErrorResponse("您，已经注册了!")
        with transaction(db_writer) as trans:
            is_ok, msg = dao.register(db_writer, safe_vars.username, safe_vars.password)
            if not is_ok:
                ErrorResponse(msg)
            trans.finish()

            session[const.SESSION.KEY_LOGIN] = is_ok
            session[const.SESSION.KEY_ADMIN_ID] = msg["user_id"]
            session[const.SESSION.KEY_ROLE_ID] = msg["role_id"]
            session[const.SESSION.KEY_ADMIN_NAME] = msg["username"]
            session.permanent = True
            log.get("auth").info(u" %s 注册成功 编号[ %s ]", safe_vars.username, msg["user_id"])
            return OkResponse()


@home.route("/login", methods=['POST'])
@general("登录")
@db_conn("db_reader")
@form_check({
    "username": F_str("用户名") & "strict" & "required",
    "password": F_str("密码") & "strict" & "required",
})
def login(db_reader, safe_vars):
    account = dao.get_account_by_username(db_reader, safe_vars.username)
    if not account:
        return ErrorResponse("用户尚未注册")

    hash_pwd = util.hash_password(safe_vars.password, safe_vars.username)
    if hash_pwd != account.password:
        return ErrorResponse("密码错误")

    session[const.SESSION.KEY_LOGIN] = True
    session[const.SESSION.KEY_ADMIN_ID] = account.id
    session[const.SESSION.KEY_ROLE_ID] = account.role_id
    session[const.SESSION.KEY_ADMIN_NAME] = account.username
    session.permanent = True
    log.get("auth").info(u" %s 登录成功 编号[ %s ]", safe_vars.username, account.id)
    return OkResponse()


@home.route("/captcha/image")
@general("获取图形验证码")
def get_image_captcha():
    captcha = ImageCaptcha()
    captcha_code = str(random.randint(1000, 9999))
    image = captcha.generate(captcha_code)
    session[const.SESSION.KEY_CAPTCHA] = captcha_code
    return send_file(image)


@home.route("/captcha/image/check")
@general("图片验证码验证")
@form_check({
    "image_captcha": F_str("图片验证码") & "strict" & "required",
})
def check_image_captcha(safe_vars):
    if safe_vars.image_captcha == session.get(const.SESSION.KEY_CAPTCHA):
        return OkResponse()
    return ErrorResponse("图片验证码错误，请重新输入")


@home.route("/download/client")
@general("采集客户端下载")
def download_client():
    path = os.path.join(os.path.dirname(home.root_path), 'upload')
    return send_from_directory(path, 'EasyDSS_v7.0.2.rar', as_attachment=True)


@home.route("/download/apk")
@general("apk下载")
def download_apk():
    path = os.path.join(os.path.dirname(home.root_path), 'upload')
    return send_from_directory(path, 'Webcam_debug-v1.0.0-c9.apk', as_attachment=True)


@home.route("/apk/qrcode")
@general("apk二维码")
def apk_qrcode():
    apk_location = util.LOCAL.REALM + "/download/apk"

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=16,
        border=4
    )
    qr.add_data(apk_location)
    img = qr.make_image().convert("RGBA")

    img_io = StringIO()
    img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png")


@home.route("/logout")
@general("注销")
@login_required()
@recognize_device()
def logout(device_type):
    session.pop(const.SESSION.KEY_LOGIN, None)
    if device_type == const.DEVICE.NAME_DICT[const.DEVICE.ANDOID]:
        return redirect(url_for("home.app_index"))
    return redirect(url_for("home.index"))
