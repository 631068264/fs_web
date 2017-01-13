#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ACCOUNT_STATUS(object):
    # 正常状态
    NORMAL = 0
    # 账号删除
    DELETED = 1


class ROLE(object):
    # 这里的ID和名字需要和数据库同步

    ADMIN = 0
    NORMAL_ACCOUNT = 1

    NAME_DICT = {
        ADMIN: "管理员",
        NORMAL_ACCOUNT: "普通用户",
    }
    ALL = NAME_DICT.keys()

    # 用户限制
    SIZE = {
        ADMIN: 52428800,  # 50M
        NORMAL_ACCOUNT: 20971520,  # 20M
    }
    # 设备个数
    DEVICE = {
        ADMIN: 10,  # 50M
        NORMAL_ACCOUNT: 2,  # 20M
    }


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


class TYPE(object):
    # 图片
    PHOTOGRAPH = 0
    # 视频
    VIDEO = 1
    NAME_DICT = {
        PHOTOGRAPH: "图片",
        VIDEO: "视频",
    }
    ALL = NAME_DICT.keys()


class SRC_STATUS(object):
    # 正常状态
    NORMAL = 0
    # 删除
    DELETED = 1


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


class DEVICE(object):
    # 接入设备
    ANDOID = "android"
    WINDOWS = "windows"
    IPHONE = "iphone"

    APP = "app"
    PC = "pc"

    NAME_DICT = {
        ANDOID: APP,
        WINDOWS: PC,
        IPHONE: APP,
    }
    ALL = NAME_DICT.keys()


class BLOCK(object):
    BLOCK = 'block'


if __name__ == '__main__':
    print(1)
