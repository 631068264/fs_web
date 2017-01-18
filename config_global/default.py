#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os

IS_SEND_SMS = False
DEFAULT_CAPTCHA = "1234"
PAGE_SIZE = 20

URL_SIGN_KEY = "debug-key"
JWT_SECRET = "Hahaha, I am secret."

debug = True
encoding = 'utf8'

debug_port = 5000

app_path = ''
cache_memorized_timeout = 60 * 60 * 1

# MySQL配置
db_config = {
    "db_reader": {"host": "127.0.0.1", "port": 3306, "db": "fs",
                  "user": "root", "passwd": "wuyuxi08", "charset": encoding},
    "db_writer": {"host": "127.0.0.1", "port": 3306, "db": "fs",
                  "user": "root", "passwd": "wuyuxi08", "charset": encoding},
}
ALLOWED_EXTENSIONS = set(['txt', 'mp4', 'png', 'jpg', 'jpeg', 'gif', '3gp'])
project_home = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
UPLOAD_FOLDER = os.path.join(project_home, "uploads")
# Flask配置
app_config = {
    "permanent_session_lifetime": True,
    "SESSION_COOKIE_SECURE": True,
    "jwt_secret": JWT_SECRET,

    # cache type
    # "CACHE_TYPE": "filesystem",
    "CACHE_TYPE": "redis",

    "CACHE_DEFAULT_TIMEOUT": 86400,

    # cache for redis
    "CACHE_KEY_PREFIX": "wyx_cache_",
    "CACHE_REDIS_HOST": "localhost",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_PASSWORD": "",
    "CACHE_REDIS_DB": 1,
    "UPLOAD_FOLDER": UPLOAD_FOLDER,
    # # cache for filesystem
    # "CACHE_DIR": os.path.expanduser("cache/hotgs/"),
    # "CACHE_THRESHOLD": 500 * 1000,
}

pool_coroutine_mode = True
pool_log = "pool-log"

db_conn_pool_size = (3, 10)
db_connection_idle = 60
db_pool_clean_interval = 1000
db_query_log = "query-log"

redis_config = {}
redis_max_connections = 4
cache_TTL = 300

cache_memorized_job_list_timeout = 60 * 5
cache_memorized_timeout = 60 * 10
cache_index_page_timeout = 60 * 10
cache_page_timeout = 60 * 10

log_config = [
    ["pool-log", "pool.log", "debug"],
    ["query-log", "query.log", "debug"],
    ["response-log", "response.log", "debug"],
    ["cgi-log", "cgi.log", "debug"],
]
