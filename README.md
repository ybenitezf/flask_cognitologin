# Flask-Login and Cognito integration make easy

There are many libraries that allow the integration of Flask with Cognito, most of them are based on the use of JWT to protect an API, like [Flask-Cognito](https://pypi.org/project/Flask-Cognito/) or [Flask-AWSCognito](https://pypi.org/project/Flask-AWSCognito/).

But what if you have a traditional web application, without a client side with Vue.js or React.

This extension allows you to authenticate users with Cognito and maintain the session with Flask-Login
