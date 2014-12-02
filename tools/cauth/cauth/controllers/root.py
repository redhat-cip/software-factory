#!/usr/bin/env python
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import crypt
import time
import hashlib
import base64
import urllib
import ldap
import logging
import requests

from M2Crypto import RSA

from pecan import expose, response, conf, abort, render
from pecan.rest import RestController

from cauth.model import db
from cauth.controllers import userdetails

LOGOUT_MSG = "You have been successfully logged " \
             "out of all the Software factory services."

logger = logging.getLogger(__name__)


def clean_back(value):
    # Enforce/limit redirect page
    if "jenkins" in value:
        return "/_jenkins/"
    if "redmine" in value:
        return "/_redmine/"
    return "/r/"


def signature(data):
    rsa_priv = RSA.load_key(conf.app['priv_key_path'])
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
        email = '%s@%s' % (username, conf.app['cookie_domain'])

    logger.info('Register user details.')
    udc = userdetails.UserDetailsCreator(conf)
    udc.create_user(username, email, lastname, keys)


def setup_response(username, back, email=None, lastname=None, keys=None):
    pre_register_user(username, email, lastname, keys)
    ticket = create_ticket(uid=username,
                           validuntil=(
                               time.time() + conf.app['cookie_period']))
    enc_ticket = urllib.quote_plus(ticket)
    response.set_cookie('auth_pubtkt',
                        value=enc_ticket,
                        domain=conf.app['cookie_domain'],
                        max_age=conf.app['cookie_period'],
                        overwrite=True)
    response.status_code = 303
    response.location = clean_back(back)


class GithubController(object):
    def get_access_token(self, code):
        github = conf.auth['github']
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": github['client_id'],
                "client_secret": github['client_secret'],
                "code": code,
                "redirect_uri": github['redirect_uri']},
            headers={'Accept': 'application/json'})
        jresp = resp.json()
        if 'access_token' in jresp:
            return jresp['access_token']
        elif 'error' in jresp:
            print "An error occured (%s): %s" % (
                jresp.get('error', None),
                jresp.get('error_description', None))
        return None

    def organization_allowed(self, login):
        allowed_orgs = conf.auth['github'].get('allowed_organizations')
        if allowed_orgs:
            resp = requests.get("https://api.github.com/users/%s/orgs" % login)
            user_orgs = resp.json()
            user_orgs = [org['login'] for org in user_orgs]
            allowed_orgs = allowed_orgs.split(',')
            allowed_orgs = filter(None, allowed_orgs)
            allowed = set(user_orgs) & set(allowed_orgs)
            if not allowed:
                return False
        return True

    @expose()
    def callback(self, **kwargs):
        if 'error' in kwargs:
            logger.error('GITHUB callback called with an error (%s): %s' % (
                kwargs.get('error', None),
                kwargs.get('error_description', None)))
        state = kwargs.get('state', None)
        code = kwargs.get('code', None)
        if not state or not code:
            logger.error(
                'GITHUB callback called without state or code as params.')
            abort(400)

        # Verify the state previously put in the db
        back = db.get_url(state)
        if not back:
            logger.error('GITHUB callback called with an unknown state.')
            abort(401)

        token = self.get_access_token(code)
        if not token:
            logger.error('Unable to request a token on GITHUB.')
            abort(401)

        resp = requests.get("https://api.github.com/user",
                            headers={'Authorization': 'token ' + token})
        data = resp.json()
        login = data.get('login')
        email = data.get('email')
        name = data.get('name')

        resp = requests.get("https://api.github.com/users/%s/keys" % login,
                            headers={'Authorization': 'token ' + token})
        ssh_keys = resp.json()

        if not self.organization_allowed(login):
            abort(401)

        logger.info('Client authentication on GITHUB sucsess.')
        setup_response(login, back, email, name, ssh_keys)

    @expose()
    def index(self, **kwargs):
        if 'back' not in kwargs:
            logger.error(
                'Client requests authentication via GITHUB' +
                'without back in params.')
            abort(422)
        back = kwargs['back']
        state = db.put_url(back)
        scope = 'user:email, read:public_key, read:org'
        github = conf.auth['github']
        logger.info(
            'Client requests authentication via GITHUB -' +
            'redirect to %s.' % github['redirect_uri'])
        response.status_code = 302
        response.location = github['auth_url'] + "?" + \
            urllib.urlencode({'client_id': github['client_id'],
                              'redirect_uri': github['redirect_uri'],
                              'state': state,
                              'scope': scope})


class LoginController(RestController):
    def check_valid_user(self, username, password):
        user = conf.auth.get('users', {}).get(username)
        if user:
            salted_password = user.get('password')
            if salted_password == crypt.crypt(password, salted_password):
                return user.get('mail'), user.get('lastname')

        l = conf.auth['ldap']
        conn = ldap.initialize(l['host'])
        conn.set_option(ldap.OPT_REFERRALS, 0)
        who = l['dn'] % {'username': username}
        try:
            conn.simple_bind_s(who, password)
        except (ldap.INVALID_CREDENTIALS, ldap.SERVER_DOWN):
            logger.error('Client unable to bind on LDAP invalid credentials.')
            return None
        result = conn.search_s(
            who, ldap.SCOPE_SUBTREE, '(cn=*)',
            attrlist=[l['sn'], l['mail']])
        if len(result) == 1:
            user = result[0]  # user is a tuple
            mail = user[1].get(l['mail'], [None])
            lastname = user[1].get(l['sn'], [None])
            return mail[0], lastname[0]
        # Something went wrong if no or more than one result is retrieved
        logger.error('Client unable to bind on LDAP unexpected behavior.')
        return (None, None)

    @expose()
    def post(self, **kwargs):
        logger.info('Client requests authentication via LDAP.')
        if 'back' not in kwargs:
            logger.error(
                'Client requests authentication via LDAP without' +
                'back in params.')
            abort(422)
        back = kwargs['back']
        if 'username' in kwargs and 'password' in kwargs:
            username = kwargs['username']
            password = kwargs['password']
            valid_user = self.check_valid_user(username, password)
            if not valid_user:
                logger.error(
                    'Client requests authentication via LDAP with' +
                    'wrong credentials.')
                response.status = 401
                return render(
                    'login.html',
                    dict(back=back, message='Authorization failed.'))
            email, lastname = valid_user
            logger.error(
                'Client requests authentication via LDAP success (%s).'
                % username)
            setup_response(username, back, email, lastname)
        else:
            logger.error(
                'Client requests authentication via LDAP without' +
                'credentials in params.')
            response.status = 401
            return render(
                'login.html',
                dict(back=back, message='Authorization failed.'))

    @expose(template='login.html')
    def get(self, **kwargs):
        if 'back' not in kwargs:
            kwargs['back'] = '/auth/logout'

        logger.info('Client requests the login page.')
        return dict(back=kwargs["back"], message='')

    github = GithubController()


class LogoutController(RestController):
    def final_logout(self):
        logger.info(
            'Client requests a logout. Set cookie auth_pubtkt to empty.')
        response.set_cookie('auth_pubtkt',
                            domain=conf.app.cookie_domain,
                            value=None)
        response.status_code = 200

    def gerrit_logout(self):
        logger.info('Client request a logout. Explicit logout on Gerrit')
        response.status_code = 302
        response.location = conf.logout['gerrit']['url']

    @expose(template='login.html')
    def get(self, **kwargs):
        """ Here we need to unset the auth_pubtkt cookie
        but also request an explicit logout on gerrit.
        """
        service = kwargs.get('service', None)
        if service == 'gerrit':
            # Here the call come from the inner gerrit logout link
            # so the Gerrit session has been already cleared.
            self.final_logout()
        if service == 'redmine':
            # Here the call come from the inner redmine logout link
            # We need then to close the Gerrit session.
            self.gerrit_logout()
        if not service:
            # Here the call come from the topmenu logout link
            # We need then to close the Gerrit session.
            self.gerrit_logout()
        return dict(back='/', message=LOGOUT_MSG)


class RootController(object):
    login = LoginController()
    logout = LogoutController()
