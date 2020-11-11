from flask_cognitologin.cognitologin import CognitoLogin
import flask
import pytest


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_app_unconfig(unconfig_app):
    with unconfig_app.app_context():
        CognitoLogin(unconfig_app)


def test_app_config(app):
    with app.app_context():
        cl = CognitoLogin()
        cl.init_app(app)
        assert cl.JWKS[0]['kid'] == 'key1'


def test_getSignInUrl(app):
    with app.test_request_context():
        cl = CognitoLogin(app)
        lurl = cl.getSignInUrl()
        assert app.config['COGNITO_CALLBACK_URL'] in lurl
        t = "/".join([app.config['COGNITO_DOMAIN'], 'login'])
        assert t in lurl


def test_getLogOutUrl(app):
    with app.test_request_context():
        cl = CognitoLogin(app)
        lurl = cl.getLogOutUrl()
        t = "/".join([app.config['COGNITO_DOMAIN'], 'logout'])
        assert app.config['COGNITO_CALLBACK_URL'] in lurl
        assert t in lurl


@pytest.mark.parametrize("csrf", ['somecode', 'othercode'])
def test_getIdentity(app, csrf):
    with app.test_request_context('/?state=somecode&code=somecode'):
        flask.session['mycogext_csrf_state'] = csrf
        cl = CognitoLogin(app)
        info = cl.getIdentity()

        if csrf == 'othercode':
            assert info is None
        else:
            assert info['sub'] == '3ed0096e-6ebd-4879-8786-80b662df0b12'
            assert info['email'] == 'some@example.com'


def test_checkIdentity(app, ident):
    with app.test_request_context('/'):
        cl = CognitoLogin(app)
        info = cl.checkIdentity(ident)
        if ident['at_hash'] == 'expired':
            assert info['at_hash'] == 'some-thing'
        elif ident['at_hash'] == 'valid':
            assert info['email'] == 'some@example.com'
        else:
            assert info is None
