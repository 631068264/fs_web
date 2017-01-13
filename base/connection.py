#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis

from config_global import default as config

redis_conn = redis.StrictRedis(
    connection_pool=redis.ConnectionPool(
        max_connections=config.redis_max_connections, **config.redis_config
    )
)
