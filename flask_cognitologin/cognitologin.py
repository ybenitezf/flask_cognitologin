"""Main module."""
from flask import session, request, current_app, _app_ctx_stack
from requests.auth import HTTPBasicAuth
from jose import jwt
from datetime import datetime
import requests
import os


class CognitoLogin(object):

    def __init__(self, app=None):
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the extension

        This extension need session so the ``SECRET_KEY`` should be
        configured::

            app.config['SECRET_KEY'] = 'some-secret-of-my-own'

        You also need:

        *  ``AWS_REGION``: aws region of your cognito user pool
        *  ``COGNITO_POOL_ID``:  Cognito user pool ID
        *  ``COGNITO_DOMAIN``: this is the full hostname of the cognito domain
           for example, ``mycogdomain.auth.eu-west-1.amazoncognito.com``,
           refer to `aws documentation`_
        *  ``COGNITO_CLIENT_ID``: Your cognito client ID
        *  ``COGNITO_CALLBACK_URL``: URL for the `autorization code grant`_,
           cognito will call to this URL with the user tokens
        *  ``COGNITO_CLIENT_SECRET``: Your cognito client secret

        :raises ValueError: if the config keys are missing

        .. _aws documentation: https://shorturl.at/tuwBF
        .. _autorization code grant: https://shorturl.at/pFIKR
        """
        config = app.config
        mykeys = [
            'AWS_REGION', 'COGNITO_POOL_ID', 'COGNITO_DOMAIN',
            'COGNITO_CLIENT_ID', 'COGNITO_CALLBACK_URL',
            'COGNITO_CLIENT_SECRET']
        tests = any([config.get(k) is None for k in mykeys])
        if tests:
            raise ValueError("Missing config keys for flask_cognito")
        app.teardown_appcontext(self.teardown)

    def _getCsrfState(self):
        session['mycogext_csrf_state'] = os.urandom(16).hex()

        return session['mycogext_csrf_state']

    def getSignInUrl(self):
        """Return the cognito url for login"""
        csrf_state = self._getCsrfState()
        config = current_app.config
        return (
            "https://{domain}/login?response_type=code&"
            "client_id={clientid}&state={csrf_state}&"
            "redirect_uri={callbackurl}".format(
                domain=config.get('COGNITO_DOMAIN'),
                clientid=config.get('COGNITO_CLIENT_ID'),
                csrf_state=csrf_state,
                callbackurl=config.get('COGNITO_CALLBACK_URL')
            )
        )

    def getLogOutUrl(self):
        """Return the cognito logout url"""
        config = current_app.config
        return (
            "https://{domain}/logout?response_type=code&client_id="
            "{clientid}&redirect_uri={callbackurl}".format(
                domain=config.get('COGNITO_DOMAIN'),
                clientid=config.get('COGNITO_CLIENT_ID'),
                callbackurl=config.get('COGNITO_CALLBACK_URL')
            )
        )

    def getIdentity(self):
        """Process cognito autorization code grant

        :return: the user identity or None
        :rtype: dict
        """
        csrf_state = request.args.get('state')
        code = request.args.get('code')
        config = current_app.config
        payload = {
            'grant_type': 'authorization_code',
            'client_id': config.get('COGNITO_CLIENT_ID'),
            'code': code,
            "redirect_uri": config.get('COGNITO_CALLBACK_URL')
        }
        r = requests.post(
            "https://%s/oauth2/token" % config.get('COGNITO_DOMAIN'),
            data=payload,
            auth=HTTPBasicAuth(
                config.get('COGNITO_CLIENT_ID'),
                config.get('COGNITO_CLIENT_SECRET')
            )
        )
        if r.ok and (csrf_state == session['mycogext_csrf_state']):
            self._verify(r.json()['access_token'])
            id_token = self._verify(
                r.json()['id_token'],
                access_token=r.json()['access_token'])
            ret = dict()
            ret.update(id_token)
            ret['refresh_token'] = r.json()['refresh_token']
            return ret

        return None

    def getTokens(self, refresh_token):
        """Returns the ``id_token`` and ``access_token``

        :param str refresh_token: refresh token for the user
        :returns: a ``dict`` with the keys ``id_token`` and ``access_token``
        :rtype: dict
        """
        config = current_app.config

        payload = {
            'grant_type': 'refresh_token',
            'client_id': config.get('COGNITO_CLIENT_ID'),
            'refresh_token': refresh_token
        }
        r = requests.post(
            "https://%s/oauth2/token" % config.get('COGNITO_DOMAIN'),
            data=payload,
            auth=HTTPBasicAuth(
                config.get('COGNITO_CLIENT_ID'),
                config.get('COGNITO_CLIENT_SECRET'))
        )

        if r.ok:
            return {
                'access_token': r.json()['access_token'],
                'id_token': r.json()['id_token']
            }
        else:
            return None

    def checkIdentity(self, identity):
        """Check identity claims

        If the current identity is about to expire a new one will be emitted.

        If ``identity`` does not has ``exp`` and ``refresh_token`` keys this
        returns ``None``

        :param dict identity: current user identity claims
        :returns: identity
        :rtype: dict
        """
        if 'exp' not in identity:
            return None
        if 'refresh_token' not in identity:
            return None
        expires = datetime.utcfromtimestamp(identity['exp'])
        expires_seconds = (expires - datetime.utcnow()).total_seconds()

        if expires_seconds < 0:
            refresh_token = identity['refresh_token']
            r = self.getTokens(refresh_token)

            if r:
                self._verify(r['access_token'])
                id_token = self._verify(
                    r['id_token'],
                    access_token=r['access_token'])
                ret = dict()
                ret.update(id_token)
                ret['refresh_token'] = refresh_token
                return ret
            else:
                return None

        return identity

    def _verify(self, token, access_token=None):
        """Verify a cognito JWT

        Get the key id from the header, locate it in the cognito keys
        and verify the key
        """
        header = jwt.get_unverified_header(token)
        config = current_app.config
        key = [k for k in self.JWKS if k["kid"] == header['kid']][0]
        id_token = jwt.decode(
            token, key, audience=config.get('COGNITO_CLIENT_ID'),
            access_token=access_token)
        return id_token

    def teardown(self, exception):
        pass
        # nothing todo here right now

    @property
    def JWKS(self):
        config = current_app.config
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'aws_jwkeys'):
                url = (
                    "https://cognito-idp.{}.amazonaws.com/{}/"
                    ".well-known/jwks.json").format(
                        config.get('AWS_REGION'),
                        config.get('COGNITO_POOL_ID')
                )
                ctx.aws_jwkeys = requests.get(url).json()["keys"]
            return ctx.aws_jwkeys
