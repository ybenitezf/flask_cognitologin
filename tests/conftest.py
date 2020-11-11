"""pytest config for `flask_cognitologin` package."""
from jose import jwt
import pytest
import flask
import os
import requests
import datetime

TEST_KEYS = {
    'keys': [
        {
            'alg': 'RS256', 'e': 'AQAB',
            'kid': 'key1',
            'kty': 'RSA',
            'n': 'somevalue',
            'use': 'sig'
        },
        {
            'alg': 'RS256', 'e': 'AQAB',
            'kid': 'key2',
            'kty': 'RSA',
            'n': 'somevalue',
            'use': 'sig'
        }
    ]
}


@pytest.fixture
def unconfig_app(request):
    app = flask.Flask(
        request.module.__name__, template_folder=os.path.dirname(__file__))
    app.testing = True
    return app


@pytest.fixture
def app(request):
    app = flask.Flask(
        request.module.__name__, template_folder=os.path.dirname(__file__))
    app.testing = True
    app.config['AWS_REGION'] = 'some-region'
    app.config['COGNITO_POOL_ID'] = 'some-pool-id'
    app.config['COGNITO_CLIENT_ID'] = 'myclient-id'
    app.config['COGNITO_DOMAIN'] = 'mypool-domain.com'
    app.config['COGNITO_CALLBACK_URL'] = 'http://127.0.0.1:5000/callback'
    app.config['COGNITO_CLIENT_SECRET'] = 'myclient-secret'
    app.config['SECRET_KEY'] = 'test-secret'
    with app.app_context():
        yield app


class JWKSResponse():

    @staticmethod
    def json():
        return TEST_KEYS


class OAUTHResponse():

    ok = True

    @staticmethod
    def json():
        return {
            'id_token': 'fake-id-token',
            'access_token': 'fake-access-token',
            'refresh_token': 'fake-refresh-token',
        }


@pytest.fixture(autouse=True)
def path_requests(monkeypatch):

    def mock_get(*args, **kwargs):
        if 'jwks.json' in args[0]:
            return JWKSResponse()

        return None

    def mock_post(*args, **kwargs):
        if 'oauth2/token' in args[0]:
            return OAUTHResponse()

        return None

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)


@pytest.fixture(params=["expired", "valid", "no-exp", "no-refresh"])
def ident(request):
    date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    exp_date = (
        date.toordinal() - datetime.date(1970, 1, 1).toordinal()
    ) * 24 * 60 * 60
    data = {
        'expired': {
            'at_hash': request.param,
            'sub': '3ed0096e-6ebd-4879-8786-80b662df0b12',
            'cognito:groups': ['SomeGroup'],
            'email_verified': True,
            'iss': 'https://some-idp.com',
            'cognito:username': 'someuser',
            'aud': '3puu67sh8ildpkfueup57qs7sc',
            'token_use': 'id',
            'auth_time': 1605032803,
            'name': 'Jhon Doe',
            'exp': 1605033103,
            'iat': 1605032803,
            'email': 'some@example.com',
            'refresh_token': 'fake-refresh-token'
        },
        'valid': {
            'at_hash': request.param,
            'sub': '3ed0096e-6ebd-4879-8786-80b662df0b12',
            'cognito:groups': ['SomeGroup'],
            'email_verified': True,
            'iss': 'https://some-idp.com',
            'cognito:username': 'someuser',
            'aud': '3puu67sh8ildpkfueup57qs7sc',
            'token_use': 'id',
            'auth_time': 1605032803,
            'name': 'Jhon Doe',
            'exp': exp_date,
            'iat': 1605032803,
            'email': 'some@example.com',
            'refresh_token': 'fake-refresh-token'
        },
        'no-exp': {
            'at_hash': request.param,
            'refresh_token': 'fake-refresh-token'
        },
        'no-refresh': {
            'at_hash': request.param,
            'exp': 1605033103,
        }
    }

    return data[request.param]


@pytest.fixture(autouse=True)
def path_jwt(monkeypatch):

    def header(token):
        return TEST_KEYS['keys'][0]

    def decode(*args, **kwargs):
        return {
            'at_hash': 'some-thing',
            'sub': '3ed0096e-6ebd-4879-8786-80b662df0b12',
            'cognito:groups': ['SomeGroup'],
            'email_verified': True,
            'iss': 'https://some-idp.com',
            'cognito:username': 'someuser',
            'aud': '3puu67sh8ildpkfueup57qs7sc',
            'token_use': 'id',
            'auth_time': 1605032803,
            'name': 'Jhon Doe',
            'exp': 1605033103,
            'iat': 1605032803,
            'email': 'some@example.com'
        }

    monkeypatch.setattr(jwt, 'get_unverified_header', header)
    monkeypatch.setattr(jwt, 'decode', decode)
