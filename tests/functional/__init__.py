import config
import json
import requests


def get_cookie(username, password):
    url = "http://%(auth_url)s/login" % {'auth_url': config.AUTH_HOST}
    resp = requests.post(url, params={'username': username,
                                      'password': password,
                                      'back': '/'},
                         allow_redirects=False)
    return resp.cookies['auth_pubtkt']


def assign_cookies():
    for k, v in config.USERS.items():
        v['auth_cookie'] = get_cookie(k,
                                      v['password'])


def create_gerrit_user(user):
    url = "%(gerrit_url)sa/accounts/%(user)s" % \
          {'gerrit_url': config.GERRIT_SERVER,
           'user': user}
    admin_cookie = config.USERS[config.ADMIN_USER]['auth_cookie']

    r = requests.get(url, cookies=dict(auth_pubtkt=admin_cookie))
    if r.status_code == 200:
        return

    assert r.status_code == 404

    # login to create an account
    user_cookie = config.USERS[user]['auth_cookie']
    url = "%(gerrit_url)slogin" % \
          {'gerrit_url': config.GERRIT_SERVER}
    requests.get(url, cookies=dict(auth_pubtkt=user_cookie),
                 allow_redirects=False)

    # set the name
    url = "%(gerrit_url)sa/account/self/name" % \
          {'gerrit_url': config.GERRIT_SERVER}
    data = json.dumps({'name': user})
    requests.put(url, cookies=dict(auth_pubtkt=user_cookie),
                 allow_redirects=False,
                 headers={"Content-Type": "application/json"},
                 data=data)

    url = "%(gerrit_url)sa/accounts/%(user)s/emails/%(email_id)s" % \
          {'gerrit_url': config.GERRIT_SERVER,
           'user': user,
           'email_id': config.USERS[user]['email']}
    data = json.dumps({'email': config.USERS[user]['email'],
                       'no_confirmation': True,
                       'preferred': True})
    requests.put(url, cookies=dict(auth_pubtkt=admin_cookie),
                 allow_redirects=False,
                 headers={"Content-Type": "application/json"},
                 data=data)


def setup():
    assign_cookies()
    for k, v in config.USERS.items():
        if k != config.ADMIN_USER:
            create_gerrit_user(k)
