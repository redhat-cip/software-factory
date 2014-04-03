from managesf import templates
from pecan import abort
import requests as http


def send_request(url, expect_return,
                 method='PUT',
                 **kwargs):
    meth = http.put
    if method == 'GET':
        meth = http.get
    elif method == 'DELETE':
        meth = http.delete
    elif method == 'POST':
        meth = http.post
    resp = meth(url, **kwargs)
    if resp.status_code not in expect_return:
        print "    Request " + method + " " + url + \
              " failed with status code " + \
              str(resp.status_code) + " - " + resp.text

        abort(resp.status_code)

    return resp


def template(t):
    return templates.__path__[0] + '/' + t
