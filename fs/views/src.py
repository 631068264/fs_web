#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'wuyuxi'

import re

from flask import Blueprint, session

from base import dao
from base.framework import general, TempResponse, db_conn, form_check, OkResponse, ErrorResponse
from base.decorator import login_required, recognize_device
from base.poolmysql import transaction
from base.smartsql import Table as T, Field as F, Expr as E, QuerySet as QS
from base import constant as const
from base.xform import F_str
from base import util

src = Blueprint("src", __name__)


@src.route("/src/list/load", methods=["POST", "GET"])
@general("资源列表")
@login_required()
@db_conn("db_reader")
@recognize_device()
@form_check({
    "begin_time": F_str("起始时间") & "strict" & "optional",
    "end_time": F_str("结束时间") & "strict" & "optional",
    "device_id": F_str("设备ID") & "strict" & "optional",
    "type": F_str("请求类型") & "optional",
})
def src_list(db_reader, safe_vars, device_type):
    templ_name = "/src_list.html"
    if safe_vars.type == const.BLOCK.BLOCK:
        templ_name = "/src_list_block.html"

    account_id = session[const.SESSION.KEY_ADMIN_ID]
    devices = dao.get_devices_by_account_id(db_reader, account_id)

    msg, is_ok = check_condition(safe_vars)
    if not is_ok:
        return TempResponse(device_type + templ_name,
                            begin_time=safe_vars.begin_time,
                            end_time=safe_vars.end_time,
                            error_msg=msg,
                            devices=devices,
                            device_id=safe_vars.device_id)
    video_srcs = None
    photo_srcs = None
    srcs = None

    if device_type == const.DEVICE.PC:
        srcs = dao.search_srcs(db_reader, account_id, safe_vars.begin_time,
                               safe_vars.end_time, safe_vars.device_id)
    elif device_type == const.DEVICE.APP:
        video_srcs = dao.get_srcs_by_type(db_reader, account_id, const.TYPE.VIDEO)
        photo_srcs = dao.get_srcs_by_type(db_reader, account_id, const.TYPE.PHOTOGRAPH)

    return TempResponse(device_type + templ_name,
                        srcs=srcs,
                        devices=devices,
                        device_id=safe_vars.device_id,
                        begin_time=safe_vars.begin_time,
                        end_time=safe_vars.end_time,
                        error_msg=None if srcs else "没有相关信息",
                        video_srcs=video_srcs,
                        photo_srcs=photo_srcs)


# TODO：回收站封禁
@src.route("/src/cancel", methods=["POST"])
@general("单资源删除")
@login_required()
@db_conn("db_writer")
@form_check({
    "src_id": F_str("资源ID") & "strict" & "required",
})
def src_cancel(db_writer, safe_vars):
    account_id = session[const.SESSION.KEY_ADMIN_ID]
    with transaction(db_writer) as trans:
        src = dao.update_src_by_account_id(db_writer, account_id, safe_vars.src_id)
        if not src:
            return ErrorResponse("该资源不是你的")

        QS(db_writer).table(T.src).where(F.id == safe_vars.src_id).update({
            "status": const.SRC_STATUS.DELETED,
        })

        QS(db_writer).table(T.account).where(F.id == account_id).update({
            "size": E("IF((size - %d ) < 0,0,size - %d)" % (src.size, src.size)),
        })
        trans.finish()
    return OkResponse()


@src.route("/batch/delete/src", methods=["POST"])
@general("资源批量删除")
@login_required()
@db_conn("db_writer")
@form_check({
    "src_id": F_str("资源ID") & "strict" & "required" & "multiple",
})
def batch_delete_src(db_writer, safe_vars):
    account_id = session[const.SESSION.KEY_ADMIN_ID]
    srcs_id = safe_vars.src_id
    with transaction(db_writer) as trans:
        srcs = dao.update_srcs(db_writer, account_id, srcs_id)
        if not srcs or len(srcs_id) != len(srcs):
            return ErrorResponse("该资源不是你的")

        QS(db_writer).table(T.src).where(F.id == srcs_id).update({
            "status": const.SRC_STATUS.DELETED,
        })

        size = 0
        for src in srcs:
            size += src.size

        QS(db_writer).table(T.account).where(F.id == account_id).update({
            "size": E("IF((size - %d ) < 0,0,size - %d)" % (size, size)),
        })
        trans.finish()
    return OkResponse()


def check_condition(var):
    begin_time = var.begin_time
    end_time = var.end_time

    if (not begin_time and end_time) or (begin_time and not end_time):
        return "请填写完整的日期", False

    if get_time(begin_time) > get_time(end_time):
        return "查询失败！ 起始日期大于结束日期", False
    else:
        return "", True


def get_time(time):
    if not time:
        return None
    time = re.match(r'(\w{4}-\w{2}-\w{2})T(\w{2}:\w{2})', time).groups()
    time = str(time[0] + " " + time[1])
    return util.str_to_time(time, format="%Y-%m-%d %H:%M")
