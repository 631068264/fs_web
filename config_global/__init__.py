# -*- coding: utf-8 -*-

"""
SplitSettings for ugame project.

__init__.py merges default.py, <WSGI_CONFIG_MODULE>.py,
<uid>.py, in that order.

default.py is a default config module.

WSGI_CONFIG_MODULE is a env, it can be setted in
uwsgi config file:
* local, for development enviroment.
* online, for online enviroment.

<uid> is current user. <uid>.py is for specified user.
It should be in .gitignore.
"""

import os


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.iteritems():
        if key in to_dict.keys() and \
                isinstance(to_dict[key], dict) and \
                isinstance(value, dict):
            deep_update(value, to_dict[key])
        else:
            to_dict[key] = value


env = os.environ.get("WSGI_CONFIG_MODULE", "local")

modules = ("default", env, "my")
current = __name__
for module_name in modules:
    try:
        module = getattr(__import__(current, globals(), locals(),
                                    [module_name]), module_name)
    except AttributeError:
        continue

    module_fg = {}
    for fg in dir(module):
        if fg.startswith("__") and fg.endswith("__"):
            continue
        module_fg[fg] = getattr(module, fg)
    deep_update(module_fg, locals())
