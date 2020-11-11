=====
Usage
=====

To use Flask-CognitoLogin in a project::

    from flask import Flask, redirect, session, url_for
    from flask_login import LoginManager, UserMixin
    from flask_login import login_required, login_user
    from flask_cognitologin import CognitoLogin

    app = Flask(__name__)

    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'some-secret'
    app.config['AWS_REGION'] = 'eu-west-1'
    app.config['COGNITO_POOL_ID'] = 'eu-west-SOMEID'
    app.config['COGNITO_DOMAIN'] = 'example.auth.eu-west-1.amazoncognito.com'
    app.config['COGNITO_CLIENT_ID'] = 'your-client-id'
    app.config['COGNITO_CALLBACK_URL'] = 'http://localhost:5000/callback'
    app.config['COGNITO_CLIENT_SECRET'] = 'supersecret'

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    cognito_login = CognitoLogin(app)


    class MyUser(UserMixin):
        pass


    @app.route('/')
    @login_required
    def hello_world():
        return 'Hello, World with cognito!'


    @app.route('/login')
    def login():
        # redirecto to cognito domain
        return redirect(cognito_login.getSignInUrl())


    @app.route('/callback')
    def callback_from_cognito():
        identity = cognito_login.getIdentity()
        if identity is not None:
            # in identity we have the claims
            u = MyUser()
            u.id = identity['sub']
            # save the identity in the session
            session['identity'] = dict()
            session['identity'].update(identity)
            # login the user
            login_user(u)
            # redirecto to the protected area
            return redirect(url_for('hello_world'))

        # something was wrong
        return 'You got not access', 403


    @login_manager.user_loader
    def load_user(user_id):
        if 'identity' not in session:
            return None

        # check expiration and identity, this call will
        # refresh the claims if it can.
        idt = cognito_login.checkIdentity(session['identity'])
        if idt is not None:
            # set/update the identity information
            session['identity'] = idt
        else:
            return None

        user = MyUser()
        user.id = user_id
        user.roles = idt['cognito:groups']
        user.email = idt['email']
        user.name = idt['name']
        user.username = idt['cognito:username']

        return user

    if __name__ == '__main__':
        app.run(host='0.0.0.0')

