#!/usr/bin/env python
# -*- coding: utf-8 -*-


class STATUS(object):
    SUCCESS = 1
    FAIL = 0


class SESSION(object):
    # common
    KEY_LOGIN = "logined"
    KEY_ADMIN_ID = "id"
    KEY_ADMIN_NAME = "username"
    KEY_ROLE_ID = "role_id"
    KEY_CAPTCHA = "image_captcha"


class COOKIES(object):
    KEY_LOGIN_OK_REDIRECT = "LOGINOKRE"
    KEY_REGISTER_OK_REDIRECT = "REGISTEROKRE"
    KEY_PASSWORD_OK_REDIRECT = "PASSWORDOKRE"
    KEY_VIEW_JOB_DETAIL_REDIRECT = "VIEWJOBREDIRECT"


class PASSWORD_ACTION(object):
    RESET = "RESET"
    CHANGE = "CHANGE"

    ALL = (RESET, CHANGE)


class TASK_STATUS(object):
    # 正常状态
    NORMAL = 0
    # 删除状态
    DELETED = 1
    # 任务完成
    FINISHED = 2
    # 循环中
    CYCLE = 3

    NAME_DICT = {
        NORMAL: "待执行",
        DELETED: "删除",
        FINISHED: "完成",
        CYCLE: "上一个任务已完成，循环中",
    }

    ALL = NAME_DICT.keys()


class TAKE_TYPE(object):
    # 图片
    PHOTOGRAPH = 0
    # 视频
    VIDEO = 1
    # 音频
    AUDIO = 3

    NAME_DICT = {
        PHOTOGRAPH: "图片",
        VIDEO: "视频",
        AUDIO: "音频",
    }
    ALL = NAME_DICT.keys()


class CALL_TYPE(object):
    NONE = 0
    INCOMING = 1
    OUTGOING = 2

    NAME_DICT = {
        INCOMING: "进",
        OUTGOING: "出",
    }
    ALL = NAME_DICT.keys()


class DEVICE_STATUS(object):
    # 正常状态
    NORMAL = 0
    # 账号删除
    DELETED = 1

    NAME_DICT = {
        NORMAL: "正常",
        DELETED: "禁用",
    }
    ALL = NAME_DICT.keys()


class BOOLEAN(object):
    TRUE = 1
    FALSE = 0
    NAME_DICT = {
        TRUE: "是",
        FALSE: "否",
    }
    ALL = (TRUE, FALSE)
