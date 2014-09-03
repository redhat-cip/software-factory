import config

from utils import get_cookie


def assign_cookies():
    for k, v in config.USERS.items():
        v['auth_cookie'] = get_cookie(k,
                                      v['password'])


def setup():
    assign_cookies()
