from pecan import expose, response, conf, abort, render
from pecan.rest import RestController
from cauth.controllers import rsa_priv
import time
import hashlib
import base64
import urllib
import ldap
import requests as http
from cauth.model import db

LOGOUT_MSG = "You have been successfully logged " \
             "out of all the Software factory services."


def signature(data):
    dgst = hashlib.sha1(data).digest()
    sig = rsa_priv.sign(dgst, 'sha1')
    sig = base64.b64encode(sig)
    return sig


def create_ticket(**kwargs):
    ticket = ''
    for k, v in kwargs.items():
        if ticket is not '':
            ticket = ticket + ';'
        ticket = ticket + '%s=%s' % (k, v)

    ticket = ticket + ";sig=%s" % signature(ticket)
    return ticket


def setup_response(username, back):
    ticket = create_ticket(uid=username,
                           validuntil=(time.time() + conf.app.cookie_period))
    enc_ticket = urllib.quote_plus(ticket)
    response.set_cookie('auth_pubtkt',
                        value=enc_ticket,
                        domain=conf.app.cookie_domain,
                        max_age=conf.app.cookie_period,
                        overwrite=True)
    response.status_code = 303
    response.location = back


class GithubController(object):
    def get_access_token(self, state, code):
        github = conf.auth['github']
        resp = http.post("https://github.com/login/oauth/access_token",
                         params={"client_id": github['client_id'],
                                 "client_secret": github['client_secret'],
                                 "code": code,
                                 "redirect_uri": github['redirect_uri']},
                         headers={'Accept': 'application/json'})
        return resp.json()['access_token']

    @expose()
    def callback(self, **kwargs):
        state = kwargs.get('state', None)
        code = kwargs.get('code', None)
        if not state or not code:
            abort(400)

        back = db.get_url(state)
        if not back:
            abort(401)

        token = self.get_access_token(state, code)
        resp = http.get("https://api.github.com/user",
                        headers={'Authorization': 'token ' + token})
        setup_response(resp.json()['login'], back)

    @expose()
    def index(self, **kwargs):
        back = kwargs['back']
        state = db.put_url(back)
        response.status_code = 302
        github = conf.auth['github']
        response.location = github['auth_url'] + "?" + \
            urllib.urlencode({'client_id': github['client_id'],
                              'redirect_uri': github['redirect_uri'],
                              'state': state,
                              'scope': 'user, user:email'
                              })


class LoginController(RestController):
    def check_valid_user_ldap(self, username, password):
        l = conf.auth['ldap']
        conn = ldap.initialize(l['host'])
        conn.set_option(ldap.OPT_REFERRALS, 0)
        who = l['dn'] % {'username': username}
        try:
            conn.simple_bind_s(who, password)
        except ldap.INVALID_CREDENTIALS:
            return False
        return True

    @expose()
    def post(self, **kwargs):
        if 'username' in kwargs and 'password' in kwargs:
            username = kwargs['username']
            password = kwargs['password']
            back = kwargs.get('back', '/r/')
            valid_user = self.check_valid_user_ldap(username, password)
            if not valid_user:
                return render(
                    'login.html',
                    dict(back=back, message='Authorization failed.'))
            setup_response(username, back)
        else:
            return render(
                'login.html',
                dict(back=back, message='Authorization failed.'))

    @expose(template='login.html')
    def get(self, **kwargs):
        if 'back' not in kwargs:
            kwargs['back'] = '/auth/logout'

        return dict(back=kwargs["back"], message='')

    github = GithubController()


class LogoutController(RestController):
    def logout_services(self, services):
        cur_service = services[0]
        if cur_service == 'cauth' and len(services) is not 1:
            # cauth should always be the last item in the list
            services.pop(0)
            services.append(cur_service)

        if cur_service == 'cauth' and len(services) is 1:
            response.set_cookie('auth_pubtkt',
                                domain=conf.app.cookie_domain,
                                value=None)
            response.status_code = 200
            return dict(back='/r/', message=LOGOUT_MSG)

        services.pop(0)
        response.status_code = 302
        response.location = conf.logout[cur_service]['url'] + \
            "?services=" + ",".join(services)
        print '  [cauth] redirecting logout req to ' + response.location
        return dict(back='/r/', message=LOGOUT_MSG)

    @expose(template='login.html')
    def get(self, **kwargs):
        if 'service' in kwargs:
            services = list(conf.logout['services'])
            service = kwargs['service']
            if service not in services:
                abort(400)

            print '  [cauth] logout request from ' + service
            services.remove(kwargs['service'])
            return self.logout_services(services)
        elif 'services' in kwargs:
            services = kwargs['services'].split(",")
            return self.logout_services(services)
        # Fallback if no service name is given
        return self.logout_services(['gerrit', 'redmine', 'cauth'])


class RootController(object):
    login = LoginController()
    logout = LogoutController()
