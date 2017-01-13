#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'wuyuxi'
import datetime

from flask import Blueprint, session, request

from base import dao, util
from base.framework import general, TempResponse, db_conn, form_check, OkResponse, ErrorResponse
from base.decorator import login_required, recognize_device
from base.poolmysql import transaction
from base.smartsql import Table as T, Field as F, Expr as E, QuerySet as QS
from base import constant as const
from base.xform import F_str

device = Blueprint("device", __name__)


@device.route("/device/list/load")
@general("设备列表页面")
@login_required()
@db_conn("db_reader")
@recognize_device()
@form_check({
    "type": F_str("请求类型") & "optional",
})
def device_list_load(db_reader, safe_vars, device_type):
    account_id = session[const.SESSION.KEY_ADMIN_ID]
    devices = dao.get_devices_by_account_id(db_reader, account_id)
    for d in devices:
        d.device_src = util.safe_json_dumps(util.get_device_src(d.id), encoding='utf-8')
    templ_name = "/device_list.html"
    if safe_vars.type == const.BLOCK.BLOCK:
        templ_name = '/device_list_block.html'
    return TempResponse(device_type + templ_name, devices=devices)


@device.route("/device/info")
@general("设备详情")
@login_required()
@db_conn("db_reader")
@recognize_device()
@form_check({
    "device_id": F_str("设备ID") & "strict" & "required",
})
def device_info(db_reader, safe_vars, device_type):
    device = QS(db_reader).table(T.device).where(F.id == safe_vars.device_id).select_one()
    if not device:
        return ErrorResponse("设备不是你的")
    return TempResponse(device_type + "/device_info.html", device=device)


@device.route("/device/add", methods=['POST'])
@general("添加设备")
@login_required()
@db_conn("db_writer")
@form_check({
    "device_name": (F_str("设备名") <= 10) & "strict" & "required",
})
def device_add(db_writer, safe_vars):
    account_id = session[const.SESSION.KEY_ADMIN_ID]

    device_num = dao.get_account_by_id(db_writer, account_id).device_num
    if device_num >= const.ROLE.DEVICE[session[const.SESSION.KEY_ROLE_ID]]:
        return ErrorResponse("用户设备过多,不能再增加")
    is_ok, msg = device_name_check(db_writer, account_id, safe_vars.device_name)
    if not is_ok:
        ErrorResponse(msg)

    with transaction(db_writer) as trans:
        QS(db_writer).table(T.device).insert({
            "id": util.get_device(),
            "name": safe_vars.device_name,
            "status": const.DEVICE_STATUS.NORMAL,
            "account_id": account_id,
            "create_time": datetime.datetime.now(),
            "remote_addr":request.remote_addr,
        })

        QS(db_writer).table(T.account).where(F.id == account_id).update({
            "device_num": E("device_num + 1"),
        })

        trans.finish()
    return OkResponse()


@device.route("/device/edit", methods=["POST"])
@general("设备改名")
@login_required()
@db_conn("db_writer")
@form_check({
    "device_id": F_str("设备ID") & "strict" & "required",
    "device_name": (F_str("设备名") <= 10) & "strict" & "required",
})
def device_edit(db_writer, safe_vars):
    with transaction(db_writer)as trans:
        account_id = session[const.SESSION.KEY_ADMIN_ID]
        device = dao.update_device_by_account_id(db_writer, account_id, safe_vars.device_id)
        if not device:
            return ErrorResponse("没有权限修改该设备")
        is_ok, msg = device_name_check(db_writer, account_id, safe_vars.device_name)
        if not is_ok:
            ErrorResponse(msg)

        QS(db_writer).table(T.device).where(F.id == safe_vars.device_id).update({
            "name": safe_vars.device_name,
        })
        trans.finish()
    return OkResponse()


def device_name_check(db, account_id, device_name):
    device = dao.get_device_by_accountId_and_name(db, account_id, device_name)
    if device:
        return False, "该名字已经被您的其他设备使用，请使用其他名字"
    return True, ""


@device.route("/device/cancel", methods=["POST"])
@general("设备删除")
@login_required()
@db_conn("db_writer")
@form_check({
    "device_id": F_str("设备ID") & "strict" & "required",
})
def device_cancel(db_writer, safe_vars):
    account_id = session[const.SESSION.KEY_ADMIN_ID]
    with transaction(db_writer) as trans:
        device = dao.update_device_by_account_id(db_writer, account_id, safe_vars.device_id)
        if not device:
            return ErrorResponse("该设备不是你的")

        QS(db_writer).table(T.device).where(F.id == device.id).update({
            "status": const.DEVICE_STATUS.DELETED,
        })
        # TODO: 资源暂时不分设备
        QS(db_writer).table(T.task).where(F.device_id == device.id).update({
            "status": const.TASK_STATUS.DELETED,
        })

        QS(db_writer).table(T.account).where(F.id == account_id).update({
            "device_num": E("if(device_num - 1 < 0, 0 ,device_num - 1)"),
        })
        trans.finish()
    return OkResponse()


@device.route("/device/play")
@general("直播页面")
@login_required()
@db_conn("db_reader")
@form_check({
    "device_id": F_str("设备ID") & "strict" & "required",
})
@recognize_device()
def device_play(db_reader, safe_vars, device_type):
    account_id = session[const.SESSION.KEY_ADMIN_ID]
    device = dao.get_device_by_account_id(db_reader, account_id, safe_vars.device_id)
    if not device:
        return ErrorResponse("还没有申请设备")
    device_src = util.get_device_src(device.id)
    print(device_src)
    return TempResponse(device_type + "/play_load.html", device=device, device_src=device_src)
