from pecan import expose, response, conf, abort, render
from pecan.rest import RestController
from cauth.controllers import rsa_priv
import time
import hashlib
import base64
import urllib
import ldap
from mockldap import LDAPObject
import requests as http
from cauth.model import db
from cauth.controllers import userdetails
import httmock
import urlparse


LOGOUT_MSG = "You have been successfully logged " \
             "out of all the Software factory services."


def clean_back(value):
    # Enforce/limit redirect page
    if "jenkins" in value:
        return "/_jenkins/"
    if "redmine" in value:
        return "/_redmine/"
    return "/r/"


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


def pre_register_user(username, email=None, lastname=None, keys=None):
    if lastname is None:
        lastname = 'User %s' % username
    if email is None:
        email = '%s@%s' % (username, conf.app.cookie_domain)

    udc = userdetails.UserDetailsCreator(conf)
    udc.create_user(username, email, lastname, keys)


def setup_response(username, back, email=None, lastname=None, keys=None):
    pre_register_user(username, email, lastname, keys)
    ticket = create_ticket(uid=username,
                           validuntil=(time.time() + conf.app.cookie_period))
    enc_ticket = urllib.quote_plus(ticket)
    response.set_cookie('auth_pubtkt',
                        value=enc_ticket,
                        domain=conf.app.cookie_domain,
                        max_age=conf.app.cookie_period,
                        overwrite=True)
    response.status_code = 303
    response.location = clean_back(back)


def dummy_ldap():
    com     = ('dc=com', {'dc': 'com'})
    example = ('dc=example,dc=com', {'dc': 'example'})
    users = ('ou=Users,dc=example,dc=com', {'ou': 'Users'})
    user1   = ('cn=user1,ou=Users,dc=example,dc=com', {
        'cn': 'user1',
        'mail': ['user1@example.com'],
        'sn': ['Demo user1'],
        'userPassword': ['userpass']})
    user2   = ('cn=user2,ou=Users,dc=example,dc=com', {
        'cn': 'user2',
        'mail': ['user2@example.com'],
        'sn': ['Demo user2'],
        'userPassword': ['userpass']})
    user3   = ('cn=user3,ou=Users,dc=example,dc=com', {
        'cn': 'user3',
        'mail': ['user3@example.com'],
        'sn': ['Demo user3'],
        'userPassword': ['userpass']})
    user4   = ('cn=user4,ou=Users,dc=example,dc=com', {
        'cn': 'user4',
        'mail': ['user4@example.com'],
        'sn': ['Demo user4'],
        'userPassword': ['userpass']})
    user5   = ('cn=user5,ou=Users,dc=example,dc=com', {
        'cn': 'user5',
        'mail': ['user5@tests.dom'],
        'sn': ['Demo user5'],
        'userPassword': ['userpass']})

    directory = dict([com, example, users, user1, user2, user3, user4, user5])
    return LDAPObject(directory)

mockoauth_users = {
    "user6": {"login": "user6",
              "password": "userpass",
              "email": "user6@tests.dom",
              "name": "Demo user6",
              "ssh_keys": "",
              "code": "user6_code",
              "token": "user6_token"}
}


#@urlmatch(netloc=r'(.*\.)?oauth\.com$')
@httmock.urlmatch(netloc=r'(.*\.)?github\.com$')
def oauthmock_request(url, request):
    users = mockoauth_users
    headers = {'content-type': 'application/json'}

    if request.method == 'POST':
        code = urlparse.parse_qs(url.query)['code'][0]
        for user in users:
            if users[user]['code'] == code:
                token = users[user]['token']
                break
        content = {"access_token": token}
    else:
        for user in users:
            if users[user]['token'] in request.headers['Authorization']:
                u = user
                break
        if 'keys' in url.path:
            content = {'key': users[u]['ssh_keys']}
        else:
            content = {'login': u,
                       'email': users[u]['email'],
                       'name': users[u]['name']}
    return httmock.response(200, content, headers, None, 5, request)


def oauth_request(method, url=None, headers=None, params=None, mockoauth=None):
    if mockoauth:
        with httmock.HTTMock(oauthmock_request):
            return method(url, headers=headers, params=params)
    else:
        return method(url, headers=headers, params=params)


class GithubController(object):
    def get_access_token(self, state, code, mockoauth):
        github = conf.auth['github']
        resp = oauth_request(http.post,
                             "https://github.com/login/oauth/access_token",
                             params={"client_id": github['client_id'],
                                     "client_secret": github['client_secret'],
                                     "code": code,
                                     "redirect_uri": github['redirect_uri']},
                             headers={'Accept': 'application/json'},
                             mockoauth=mockoauth)
        return resp.json()['access_token']

    @expose()
    def callback(self, **kwargs):
        state = kwargs.get('state', None)
        code = kwargs.get('code', None)
        mockoauth = kwargs.get('mockoauth', None)
        if not state or not code:
            abort(400)

        back = db.get_url(state)
        if not back:
            abort(401)

        token = self.get_access_token(state, code, mockoauth)
        resp = oauth_request(http.get, "https://api.github.com/user",
                             headers={'Authorization': 'token ' + token},
                             mockoauth=mockoauth)
        data = resp.json()
        login = data.get('login')
        email = data.get('email')
        name = data.get('name')
        resp = oauth_request(http.get,
                             "https://api.github.com/users/%s/keys" % login,
                             headers={'Authorization': 'token ' + token},
                             mockoauth=mockoauth)
        ssh_keys = resp.json()
        setup_response(login, back, email, name, ssh_keys)

    def mockoauth_authorize(self, username, password, state, scope):
        users = mockoauth_users
        if username not in users:
            abort(401)
        if users[username]['password'] != password:
            abort(401)
        code = users[username]['code']
        kwargs = {'state': state, 'code': code, 'mockoauth': True}
        self.callback(**kwargs)

    @expose()
    def index(self, **kwargs):
        back = kwargs['back']
        state = db.put_url(back)
        #mock oauth for functional tests
        if (conf.auth['github']['top_domain'] == 'tests.dom') and \
           ('username' in kwargs):
                username = kwargs['username']
                password = kwargs['password']
                scope = 'user, user:email'
                self.mockoauth_authorize(username, password, state, scope)
        else:
            response.status_code = 302
            github = conf.auth['github']
            response.location = github['auth_url'] + "?" + \
                urllib.urlencode({'client_id': github['client_id'],
                                  'redirect_uri': github['redirect_uri'],
                                  'state': state,
                                  'scope': 'user, user:email'})


class LoginController(RestController):
    def check_valid_user_ldap(self, username, password):
        l = conf.auth['ldap']
        if l['host'] == 'ldap://ldap.tests.dom':
            conn = dummy_ldap()
        else:
            conn = ldap.initialize(l['host'])
        conn.set_option(ldap.OPT_REFERRALS, 0)
        who = l['dn'] % {'username': username}
        try:
            conn.simple_bind_s(who, password)
        except ldap.INVALID_CREDENTIALS:
            return None
        result = conn.search_s(who, ldap.SCOPE_SUBTREE, '(cn=*)', attrlist=[l['sn'],l['mail']])
        if len(result) == 1:
            user = result[0]  # user is a tuple
            mail = user[1].get(l['mail'], [None])
            lastname = user[1].get(l['sn'], [None])
            return mail[0], lastname[0]
        # Something went wrong if no or more than one result is retrieved
        return (None, None)

    @expose()
    def post(self, **kwargs):
        if 'username' in kwargs and 'password' in kwargs:
            username = kwargs['username']
            password = kwargs['password']
            if 'back' not in kwargs:
                abort(422)
            back = kwargs['back']
            valid_user = self.check_valid_user_ldap(username, password)
            if not valid_user:
                return render(
                    'login.html',
                    dict(back=back, message='Authorization failed.'))
            email, lastname = valid_user
            setup_response(username, back, email, lastname)
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
