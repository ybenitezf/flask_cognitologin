"""Main module."""
from flask import current_app, _app_ctx_stack, session, request
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
        # vefiry config's and defaults
        self.AWS_REGION = app.config['AWS_REGION']
        self.COGNITO_POOL_ID = app.config['COGNITO_POOL_ID']
        self.COGNITO_DOMAIN = app.config['COGNITO_DOMAIN']
        self.COGNITO_CLIENT_ID = app.config['COGNITO_CLIENT_ID']
        self.COGNITO_CALLBACK_URL = app.config['COGNITO_CALLBACK_URL']
        self.COGNITO_CLIENT_SECRET = app.config['COGNITO_CLIENT_SECRET']
        self._loadKeys()
        app.teardown_appcontext(self.teardown)
        self.app = app

    def _loadKeys(self):
        """load and cache cognito JSON Web Key (JWK)"""
        url = (
            "https://cognito-idp.{}.amazonaws.com/{}/"
            ".well-known/jwks.json").format(
                self.AWS_REGION, self.COGNITO_POOL_ID
            )
        self.JWKS = requests.get(url).json()["keys"]

    def _getCsrfState(self):
        session['mycogext_csrf_state'] = os.urandom(16).hex()

        return session['mycogext_csrf_state']

    def getSignInUrl(self):
        """Return the cognito URL for signin"""
        csrf_state = self._getCsrfState()
        return (
            "https://{domain}/login?response_type=code&"
            "client_id={clientid}&state={csrf_state}&"
            "redirect_uri={callbackurl}".format(
                domain=self.COGNITO_DOMAIN,
                clientid=self.COGNITO_CLIENT_ID,
                csrf_state=csrf_state,
                callbackurl=self.COGNITO_CALLBACK_URL
            )
        )

    def getLogOutUrl(self):
        """Return the cognito logout url"""
        return (
            "https://{domain}/logout?response_type=code&client_id="
            "{clientid}&redirect_uri={callbackurl}".format(
                domain=self.COGNITO_DOMAIN,
                clientid=self.COGNITO_CLIENT_ID,
                callbackurl=self.COGNITO_CALLBACK_URL
            )
        )

    def getUserInfo(self):
        """Call this on COGNITO_CALLBACK_URL to get the user info
        
        returns a dict with the keys of the claims of the id_token and
        access_token:

        {
            "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "cognito:groups": ["SomeGroup", ...],
            "email_verified": True,
            "cognito:username": "lolo",
            "name": "Lolo Perez", 
            "exp": 1604608415,
            "email": "ybenitezf@gmail.com"
            ...
        }
        """
        csrf_state = request.args.get('state')
        code = request.args.get('code')
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.COGNITO_CLIENT_ID,
            'code': code,
            "redirect_uri" : self.COGNITO_CALLBACK_URL
        }
        r = requests.post(
            "https://%s/oauth2/token" % self.COGNITO_DOMAIN,
            data=payload,
            auth=HTTPBasicAuth(
                self.COGNITO_CLIENT_ID, self.COGNITO_CLIENT_SECRET)
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

    def loadUserInfo(self, identity):
        """Load the user from the session if any
        
        If there is no user return None

        If the access has expired it will try to get new tokens and updates
        the user identity

        Return's user identity claims

        {
            "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "cognito:groups": ["SomeGroup", ...],
            "email_verified": True,
            "cognito:username": "lolo",
            "name": "Lolo Perez", 
            "exp": 1604608415,
            "email": "ybenitezf@gmail.com"
            ...
        }
        """
        if 'exp' not in identity:
            return None
        if 'refresh_token' not in identity:
            return None
        expires = datetime.utcfromtimestamp(identity['exp'])
        expires_seconds = (expires - datetime.utcnow()).total_seconds()

        if expires_seconds < 0:
            refresh_token = identity['refresh_token']
            payload = {
                'grant_type': 'refresh_token',
                'client_id': self.COGNITO_CLIENT_ID,
                'refresh_token': refresh_token
            }
            r = requests.post(
                "https://%s/oauth2/token" % self.COGNITO_DOMAIN,
                data=payload,
                auth=HTTPBasicAuth(
                    self.COGNITO_CLIENT_ID, self.COGNITO_CLIENT_SECRET)
            )

            if r.ok:
                self._verify(r.json()['access_token'])
                id_token = self._verify(
                    r.json()['id_token'], 
                    access_token=r.json()['access_token'])
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
        key = [k for k in self.JWKS if k["kid"] == header['kid']][0]
        id_token = jwt.decode(
            token, key, audience=self.COGNITO_CLIENT_ID, 
            access_token=access_token)
        return id_token


    def teardown(self, exception):
        pass
        # nothing todo here right now
